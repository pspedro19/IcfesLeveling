'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Search, 
  BookOpen, 
  Video, 
  Clock, 
  Target, 
  TrendingUp,
  Filter,
  Play,
  ExternalLink,
  Star,
  Zap
} from 'lucide-react';
import { icfesCatalogService, ICFESArea, ICFESTopic, ICFESVideo } from '../services/icfes-catalog.service';

interface ICFESCatalogViewerProps {
  className?: string;
  onTopicSelect?: (topic: ICFESTopic) => void;
  showVideos?: boolean;
}

export default function ICFESCatalogViewer({ 
  className = '', 
  onTopicSelect,
  showVideos = true 
}: ICFESCatalogViewerProps) {
  const [areas, setAreas] = useState<ICFESArea[]>([]);
  const [selectedArea, setSelectedArea] = useState<string>('');
  const [topics, setTopics] = useState<ICFESTopic[]>([]);
  const [videos, setVideos] = useState<ICFESVideo[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<ICFESTopic[]>([]);
  const [difficultyFilter, setDifficultyFilter] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  // Cargar áreas al montar el componente
  useEffect(() => {
    loadAreas();
  }, []);

  // Cargar temas cuando cambie el área seleccionada
  useEffect(() => {
    if (selectedArea) {
      loadAreaData(selectedArea);
    }
  }, [selectedArea]);

  const loadAreas = async () => {
    setLoading(true);
    try {
      const areasData = await icfesCatalogService.getAreas();
      setAreas(areasData);
      if (areasData.length > 0) {
        setSelectedArea(areasData[0].code);
      }
    } catch (error) {
      console.error('Error cargando áreas:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAreaData = async (areaCode: string) => {
    setLoading(true);
    try {
      const [topicsData, videosData] = await Promise.all([
        icfesCatalogService.getTopicsByArea(areaCode, difficultyFilter || undefined),
        showVideos ? icfesCatalogService.getYouTubeVideosByArea(areaCode) : []
      ]);
      
      setTopics(topicsData);
      setVideos(videosData);
    } catch (error) {
      console.error('Error cargando datos del área:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    setLoading(true);
    try {
      const results = await icfesCatalogService.searchTopics(
        searchQuery, 
        selectedArea || undefined, 
        difficultyFilter || undefined
      );
      setSearchResults(results?.results || []);
    } catch (error) {
      console.error('Error en búsqueda:', error);
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleTopicClick = (topic: ICFESTopic) => {
    if (onTopicSelect) {
      onTopicSelect(topic);
    }
  };

  const getDifficultyColor = (difficulty: number) => {
    switch (difficulty) {
      case 1: return 'bg-green-100 text-green-800';
      case 2: return 'bg-yellow-100 text-yellow-800';
      case 3: return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getDifficultyLabel = (difficulty: number) => {
    switch (difficulty) {
      case 1: return 'Básico';
      case 2: return 'Intermedio';
      case 3: return 'Avanzado';
      default: return 'N/A';
    }
  };

  const getWeightColor = (weight: number) => {
    if (weight >= 0.35) return 'text-red-600 font-bold';
    if (weight >= 0.30) return 'text-orange-600 font-semibold';
    return 'text-blue-600';
  };

  const formatTime = (minutes: number) => {
    if (minutes < 60) return `${minutes} min`;
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}min` : `${hours}h`;
  };

  const currentArea = areas.find(a => a.code === selectedArea);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header con estadísticas */}
      <Card className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 border-purple-500">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-gold-500">
            <BookOpen className="w-6 h-6" />
            Catálogo ICFES Completo
          </CardTitle>
          <p className="text-purple-300">
            Explora todos los temas, videos y recursos disponibles para tu preparación ICFES
          </p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {areas.map((area) => (
              <div
                key={area.code}
                className={`text-center p-3 rounded-lg cursor-pointer transition-all ${
                  selectedArea === area.code
                    ? 'bg-purple-600/30 border-purple-500 border-2'
                    : 'bg-black/30 border border-purple-500/30 hover:border-purple-500/60'
                }`}
                onClick={() => setSelectedArea(area.code)}
              >
                <div className="text-lg font-bold text-gold-400">{area.code}</div>
                <div className="text-sm text-purple-300">{area.name}</div>
                <div className="text-xs text-gray-400 mt-1">
                  {area.topic_count} temas • {formatTime(area.estimated_total_time)}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Tabs de navegación */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4 bg-black/50 backdrop-blur-sm">
          <TabsTrigger value="overview">Vista General</TabsTrigger>
          <TabsTrigger value="topics">Temas</TabsTrigger>
          <TabsTrigger value="videos">Videos</TabsTrigger>
          <TabsTrigger value="search">Búsqueda</TabsTrigger>
        </TabsList>

        {/* Tab: Vista General */}
        <TabsContent value="overview" className="mt-6">
          <Card className="bg-black/30 backdrop-blur-md border-purple-500">
            <CardHeader>
              <CardTitle className="text-gold-500">
                {currentArea?.name} - Resumen del Área
              </CardTitle>
            </CardHeader>
            <CardContent>
              {currentArea && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center p-4 bg-purple-900/20 rounded-lg border border-purple-500/30">
                    <Target className="w-8 h-8 text-purple-400 mx-auto mb-2" />
                    <div className="text-2xl font-bold text-gold-400">{currentArea.topic_count}</div>
                    <div className="text-purple-300">Temas Disponibles</div>
                  </div>
                  
                  <div className="text-center p-4 bg-blue-900/20 rounded-lg border border-blue-500/30">
                    <Video className="w-8 h-8 text-blue-400 mx-auto mb-2" />
                    <div className="text-2xl font-bold text-blue-400">{videos.length}</div>
                    <div className="text-blue-300">Videos YouTube</div>
                  </div>
                  
                  <div className="text-center p-4 bg-green-900/20 rounded-lg border border-green-500/30">
                    <Clock className="w-8 h-8 text-green-400 mx-auto mb-2" />
                    <div className="text-2xl font-bold text-green-400">
                      {formatTime(currentArea.estimated_total_time)}
                    </div>
                    <div className="text-green-300">Tiempo Total</div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Temas */}
        <TabsContent value="topics" className="mt-6">
          <Card className="bg-black/30 backdrop-blur-md border-purple-500">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-gold-500">Temas de {currentArea?.name}</CardTitle>
                <div className="flex gap-2">
                  <Button
                    variant={difficultyFilter === null ? "default" : "outline"}
                    size="sm"
                    onClick={() => setDifficultyFilter(null)}
                  >
                    Todos
                  </Button>
                  <Button
                    variant={difficultyFilter === 1 ? "default" : "outline"}
                    size="sm"
                    onClick={() => setDifficultyFilter(1)}
                  >
                    Básico
                  </Button>
                  <Button
                    variant={difficultyFilter === 2 ? "default" : "outline"}
                    size="sm"
                    onClick={() => setDifficultyFilter(2)}
                  >
                    Intermedio
                  </Button>
                  <Button
                    variant={difficultyFilter === 3 ? "default" : "default"}
                    size="sm"
                    onClick={() => setDifficultyFilter(3)}
                  >
                    Avanzado
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold-500 mx-auto"></div>
                  <p className="text-purple-300 mt-2">Cargando temas...</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {topics.map((topic) => (
                    <motion.div
                      key={topic.code}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className="border border-purple-500/30 rounded-lg p-4 hover:border-purple-500/60 hover:shadow-[0_0_10px_#8a2be2] transition-all cursor-pointer bg-black/40 backdrop-blur-sm"
                      onClick={() => handleTopicClick(topic)}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <h4 className="font-semibold text-gold-300 text-sm">{topic.main_topic}</h4>
                        <Badge className={getDifficultyColor(topic.difficulty)}>
                          {getDifficultyLabel(topic.difficulty)}
                        </Badge>
                      </div>
                      
                      <div className="space-y-2 text-xs">
                        <div className="flex items-center gap-2 text-purple-300">
                          <TrendingUp className="w-3 h-3" />
                          <span className={getWeightColor(topic.icfes_weight)}>
                            Peso ICFES: {(topic.icfes_weight * 100).toFixed(0)}%
                          </span>
                        </div>
                        
                        <div className="flex items-center gap-2 text-blue-300">
                          <Clock className="w-3 h-3" />
                          <span>{formatTime(topic.estimated_time)}</span>
                        </div>
                        
                        {topic.youtube_url && (
                          <div className="flex items-center gap-2 text-green-300">
                            <Video className="w-3 h-3" />
                            <span>Video disponible</span>
                          </div>
                        )}
                      </div>
                      
                      <div className="mt-3 pt-2 border-t border-purple-500/20">
                        <div className="text-xs text-gray-400">
                          Canal: {topic.suggested_channel}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Videos */}
        <TabsContent value="videos" className="mt-6">
          <Card className="bg-black/30 backdrop-blur-md border-purple-500">
            <CardHeader>
              <CardTitle className="text-gold-500">Videos YouTube - {currentArea?.name}</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold-500 mx-auto"></div>
                  <p className="text-purple-300 mt-2">Cargando videos...</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {videos.map((video) => (
                    <motion.div
                      key={video.topic_code}
                      whileHover={{ scale: 1.02 }}
                      className="border border-blue-500/30 rounded-lg p-4 hover:border-blue-500/60 hover:shadow-[0_0_10px_#3b82f6] transition-all bg-black/40 backdrop-blur-sm"
                    >
                      <div className="aspect-video bg-gray-900 rounded-lg mb-3 flex items-center justify-center">
                        <Play className="w-8 h-8 text-blue-400" />
                      </div>
                      
                      <h4 className="font-semibold text-gold-300 mb-2">{video.topic_name}</h4>
                      
                      <div className="space-y-2 text-xs">
                        <div className="flex items-center gap-2 text-blue-300">
                          <Video className="w-3 h-3" />
                          <span>{video.channel}</span>
                        </div>
                        
                        <div className="text-gray-400">
                          ID: {video.video_id}
                        </div>
                      </div>
                      
                      <div className="mt-3 flex gap-2">
                        <Button
                          size="sm"
                          className="flex-1 bg-blue-600 hover:bg-blue-700"
                          onClick={() => window.open(video.youtube_url, '_blank')}
                        >
                          <ExternalLink className="w-3 h-3 mr-1" />
                          Ver Video
                        </Button>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Búsqueda */}
        <TabsContent value="search" className="mt-6">
          <Card className="bg-black/30 backdrop-blur-md border-purple-500">
            <CardHeader>
              <CardTitle className="text-gold-500">Búsqueda en Catálogo ICFES</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="Buscar temas, conceptos..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    className="flex-1"
                  />
                  <Button onClick={handleSearch} disabled={loading}>
                    <Search className="w-4 h-4 mr-2" />
                    Buscar
                  </Button>
                </div>
                
                {searchResults.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-purple-300 mb-3">
                      Resultados de búsqueda: "{searchQuery}" ({searchResults.length} encontrados)
                    </h4>
                    
                    <div className="space-y-3">
                      {searchResults.map((topic) => (
                        <motion.div
                          key={topic.code}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          className="border border-purple-500/30 rounded-lg p-3 hover:border-purple-500/60 cursor-pointer bg-black/40 backdrop-blur-sm"
                          onClick={() => handleTopicClick(topic)}
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <h5 className="font-semibold text-gold-300">{topic.main_topic}</h5>
                              <div className="text-sm text-purple-300">{topic.area}</div>
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge className={getDifficultyColor(topic.difficulty)}>
                                {getDifficultyLabel(topic.difficulty)}
                              </Badge>
                              <Badge className="bg-blue-100 text-blue-800">
                                {topic.code}
                              </Badge>
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
