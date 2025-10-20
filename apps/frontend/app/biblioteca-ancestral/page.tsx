'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { 
  BookOpen, 
  Play, 
  Clock, 
  Star, 
  Target, 
  ArrowLeft,
  Filter,
  Search,
  CheckCircle
} from 'lucide-react';
import MainNavigation from '../components/Navigation/MainNavigation';

interface Video {
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

interface Subject {
  id: string;
  name: string;
  video_count: number;
  color: string;
  icon: string;
}

export default function BibliotecaAncestralPage() {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [selectedSubject, setSelectedSubject] = useState<string | null>(null);
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null);
  const [completedVideos, setCompletedVideos] = useState<Set<string>>(new Set());
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    // Load user data
    const userData = localStorage.getItem('currentUser') || localStorage.getItem('user');
    if (userData) {
      const user = JSON.parse(userData);
      setCurrentUser(user);
      
      // Check level requirement
      if (user.level < 5) {
        alert('🔒 Acceso Denegado\n\nLa Biblioteca de los Ancestros requiere Nivel 5.\nTu nivel actual: ' + user.level + '\n\n¡Completa más diagnósticos para subir de nivel!');
        router.push('/hub-central');
        return;
      }
    }
    
    loadSubjects();
  }, []);

  const loadSubjects = async () => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
      const response = await fetch(`${API_URL}/api/v1/diagnostic-public/subjects`);
      
      if (response.ok) {
        const data = await response.json();
        const subjectsWithColors = data.map((subject: any, index: number) => ({
          ...subject,
          color: getSubjectColor(subject.name),
          icon: getSubjectIcon(subject.name),
          video_count: getVideoCount(subject.name)
        }));
        setSubjects(subjectsWithColors);
      }
    } catch (error) {
      console.error('Error loading subjects:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadVideosForSubject = async (subjectId: string) => {
    try {
      setLoading(true);
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(`${API_URL}/api/v1/simple-recommendations/working-videos/${subjectId}?limit=20`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setVideos(data.working_videos || []);
        setSelectedSubject(subjectId);
      }
    } catch (error) {
      console.error('Error loading videos:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSubjectColor = (name: string) => {
    const colors = {
      'Matemáticas': 'from-blue-600 to-cyan-600',
      'Lenguaje': 'from-green-600 to-emerald-600',
      'Ciencias Naturales': 'from-emerald-600 to-teal-600',
      'Ciencias Sociales': 'from-orange-600 to-red-600',
      'Inglés': 'from-purple-600 to-pink-600'
    };
    return colors[name] || 'from-gray-600 to-slate-600';
  };

  const getSubjectIcon = (name: string) => {
    const icons = {
      'Matemáticas': '🔢',
      'Lenguaje': '📖',
      'Ciencias Naturales': '🧬',
      'Ciencias Sociales': '🏛️',
      'Inglés': '🌍'
    };
    return icons[name] || '📚';
  };

  const getVideoCount = (name: string) => {
    const counts = {
      'Matemáticas': 42,
      'Lenguaje': 28,
      'Ciencias Naturales': 54,
      'Ciencias Sociales': 39,
      'Inglés': 30
    };
    return counts[name] || 0;
  };

  const openVideoModal = (video: Video) => {
    setSelectedVideo(video);
  };

  const closeVideoModal = () => {
    setSelectedVideo(null);
  };

  const markVideoCompleted = (video: Video) => {
    setCompletedVideos(prev => new Set([...prev, video.video_id]));
    
    // Award XP (simulate)
    const xpGained = 150;
    alert(`🎉 ¡Video completado!\n\n📚 ${video.title}\n⚡ +${xpGained} XP ganados\n🏆 Progreso guardado`);
  };

  const filteredVideos = videos.filter(video => 
    video.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    video.channel_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    video.topics_covered.some(topic => topic.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  if (loading && !selectedSubject) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-gold-400 mx-auto mb-4"></div>
          <h2 className="text-2xl font-bold mb-2">📚 Accediendo a la Biblioteca...</h2>
          <p className="text-purple-200">Cargando conocimiento ancestral</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      <MainNavigation currentUser={currentUser} />
      
      <div className="pt-20 lg:pt-24 pb-8">
        <div className="container mx-auto px-4">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-8"
          >
            <div className="flex items-center justify-center gap-4 mb-4">
              <button
                onClick={() => selectedSubject ? setSelectedSubject(null) : router.push('/hub-central')}
                className="bg-purple-600/50 hover:bg-purple-700/50 p-3 rounded-lg transition-all"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              
              <h1 className="text-4xl font-bold bg-gradient-to-r from-gold-400 to-purple-400 bg-clip-text text-transparent">
                📚 Biblioteca de los Ancestros
              </h1>
            </div>
            
            <p className="text-xl text-purple-200">
              {selectedSubject 
                ? `Videos de ${subjects.find(s => s.id === selectedSubject)?.name || 'la materia seleccionada'}`
                : 'Videos y recursos de estudio por competencia ICFES'
              }
            </p>
            
            {/* Level Badge */}
            <div className="inline-flex items-center gap-2 bg-green-800/50 px-4 py-2 rounded-lg mt-4">
              <CheckCircle className="w-4 h-4 text-green-400" />
              <span className="text-green-200">Nivel 5+ Requerido - ¡Desbloqueado!</span>
            </div>
          </motion.div>

          {/* Subject Selection */}
          {!selectedSubject && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              {subjects.map((subject, index) => (
                <motion.div
                  key={subject.id}
                  initial={{ opacity: 0, y: 50 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="group cursor-pointer"
                  onClick={() => loadVideosForSubject(subject.id)}
                >
                  <div className={`bg-gradient-to-br ${subject.color}/20 rounded-xl p-6 border-2 border-purple-500/30 hover:border-gold-500/50 transition-all transform hover:scale-105 backdrop-blur-sm`}>
                    <div className="text-center">
                      <div className={`w-20 h-20 rounded-full bg-gradient-to-r ${subject.color} flex items-center justify-center text-3xl mb-4 mx-auto shadow-lg`}>
                        {subject.icon}
                      </div>
                      
                      <h3 className="text-xl font-bold text-white mb-2">{subject.name}</h3>
                      
                      <div className="flex justify-center gap-4 text-sm text-purple-200 mb-4">
                        <div className="flex items-center gap-1">
                          <Play className="w-4 h-4" />
                          {subject.video_count} videos
                        </div>
                        <div className="flex items-center gap-1">
                          <Star className="w-4 h-4" />
                          Alta calidad
                        </div>
                      </div>
                      
                      <button className={`bg-gradient-to-r ${subject.color} px-6 py-2 rounded-lg font-semibold text-white hover:shadow-lg transition-all`}>
                        🚀 Explorar
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}

          {/* Video Library */}
          {selectedSubject && (
            <>
              {/* Search and Filters */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-6 bg-black/30 rounded-xl p-4 border border-purple-500/30"
              >
                <div className="flex flex-col md:flex-row gap-4 items-center">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-purple-400" />
                    <input
                      type="text"
                      placeholder="Buscar videos por título, canal o tema..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 bg-purple-800/30 border border-purple-500/30 rounded-lg text-white placeholder-purple-300 focus:outline-none focus:border-gold-500/50"
                    />
                  </div>
                  
                  <div className="flex items-center gap-2 text-purple-200">
                    <Filter className="w-4 h-4" />
                    <span className="text-sm">{filteredVideos.length} videos encontrados</span>
                  </div>
                </div>
              </motion.div>

              {/* Videos Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredVideos.map((video, index) => {
                  const isCompleted = completedVideos.has(video.video_id);
                  
                  return (
                    <motion.div
                      key={video.video_id}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: index * 0.05 }}
                      className={`bg-gradient-to-br from-gray-900/80 to-purple-900/80 rounded-xl p-4 border ${
                        isCompleted ? 'border-green-500/50' : 'border-purple-500/30'
                      } hover:border-gold-500/50 transition-all cursor-pointer group`}
                      onClick={() => openVideoModal(video)}
                    >
                      {/* Video Thumbnail */}
                      <div className="relative mb-3">
                        <img
                          src={video.thumbnail_url}
                          alt={video.title}
                          className="w-full h-32 object-cover rounded-lg"
                          onError={(e) => {
                            e.currentTarget.src = `https://img.youtube.com/vi/${video.youtube_id}/hqdefault.jpg`;
                          }}
                        />
                        <div className="absolute inset-0 bg-black/50 rounded-lg flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                          <Play className="w-12 h-12 text-white drop-shadow-lg" />
                        </div>
                        
                        {isCompleted && (
                          <div className="absolute top-2 right-2 bg-green-500 rounded-full p-1">
                            <CheckCircle className="w-4 h-4 text-white" />
                          </div>
                        )}
                      </div>

                      {/* Video Info */}
                      <h3 className="font-bold text-white mb-2 line-clamp-2 min-h-[3rem]">
                        {video.title}
                      </h3>
                      
                      <div className="text-sm text-purple-200 mb-2">
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
                      
                      {/* Topics */}
                      <div className="flex flex-wrap gap-1 mb-3">
                        {video.topics_covered.slice(0, 2).map((topic, idx) => (
                          <span key={idx} className="text-xs bg-blue-800/50 px-2 py-1 rounded">
                            {topic}
                          </span>
                        ))}
                      </div>
                      
                      {!isCompleted ? (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            markVideoCompleted(video);
                          }}
                          className="w-full bg-green-600 hover:bg-green-700 py-2 rounded-lg text-sm font-semibold transition-colors"
                        >
                          ✅ Marcar como Visto (+150 XP)
                        </button>
                      ) : (
                        <div className="w-full bg-green-800/50 py-2 rounded-lg text-sm font-semibold text-center text-green-200">
                          ✅ Completado
                        </div>
                      )}
                    </motion.div>
                  );
                })}
              </div>
            </>
          )}

          {/* Back to Hub Button */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
            className="mt-8 text-center"
          >
            <button
              onClick={() => router.push('/hub-central')}
              className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 px-6 py-3 rounded-lg font-semibold transition-all transform hover:scale-105 flex items-center gap-2 mx-auto"
            >
              <ArrowLeft className="w-5 h-5" />
              Volver al Hub Central
            </button>
          </motion.div>
        </div>
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
            
            {!completedVideos.has(selectedVideo.video_id) && (
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
          </div>
        </div>
      )}
    </div>
  );
}
