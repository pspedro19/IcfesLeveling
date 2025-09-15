'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { 
  Play, 
  PlayCircle,
  Pause,
  SkipForward,
  SkipBack,
  Shuffle,
  Repeat,
  Plus,
  Trash2,
  Edit3,
  Share2,
  Download,
  Clock,
  Eye,
  Star,
  Bookmark,
  BookmarkPlus,
  List,
  Grid,
  Filter,
  Search,
  MoreVertical,
  CheckCircle2,
  AlertTriangle,
  Info,
  Settings,
  Volume2,
  Maximize,
  Heart,
  HeartOff,
  ExternalLink
} from 'lucide-react';

interface VideoItem {
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
  watched_percentage?: number;
  is_bookmarked?: boolean;
  is_favorite?: boolean;
  progress_seconds?: number;
}

interface Playlist {
  id: string;
  name: string;
  description?: string;
  videos: VideoItem[];
  created_at: string;
  updated_at: string;
  is_public: boolean;
  total_duration: number;
  completed_videos: number;
  tags: string[];
  subject_focus?: string;
  difficulty_level?: string;
}

interface VideoPlaylistManagerProps {
  initialVideos?: VideoItem[];
  userId: string;
  onVideoSelect?: (video: VideoItem, playlist?: Playlist) => void;
  onPlaylistChange?: (playlist: Playlist) => void;
  autoPlay?: boolean;
  showControls?: boolean;
  allowCreatePlaylist?: boolean;
  maxPlaylistSize?: number;
}

export default function VideoPlaylistManager({
  initialVideos = [],
  userId,
  onVideoSelect,
  onPlaylistChange,
  autoPlay = false,
  showControls = true,
  allowCreatePlaylist = true,
  maxPlaylistSize = 50
}: VideoPlaylistManagerProps) {
  // State management
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [currentPlaylist, setCurrentPlaylist] = useState<Playlist | null>(null);
  const [currentVideoIndex, setCurrentVideoIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playMode, setPlayMode] = useState<'normal' | 'shuffle' | 'repeat'>('normal');
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Form states
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [playlistName, setPlaylistName] = useState('');
  const [playlistDescription, setPlaylistDescription] = useState('');
  const [playlistTags, setPlaylistTags] = useState('');
  const [isPublic, setIsPublic] = useState(false);
  
  // Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [filterSubject, setFilterSubject] = useState('all');
  const [filterLevel, setFilterLevel] = useState('all');
  const [filterCompletion, setFilterCompletion] = useState('all');

  // Load user playlists
  useEffect(() => {
    loadUserPlaylists();
  }, [userId]);

  // Initialize with videos if provided
  useEffect(() => {
    if (initialVideos.length > 0 && !currentPlaylist) {
      const tempPlaylist: Playlist = {
        id: 'temp-' + Date.now(),
        name: 'Videos Recomendados',
        description: 'Lista temporal de videos recomendados',
        videos: initialVideos,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        is_public: false,
        total_duration: initialVideos.reduce((sum, video) => sum + (video.duration_seconds || 0), 0),
        completed_videos: initialVideos.filter(video => (video.watched_percentage || 0) >= 80).length,
        tags: [],
        subject_focus: initialVideos[0]?.area_evaluada
      };
      setCurrentPlaylist(tempPlaylist);
    }
  }, [initialVideos]);

  const loadUserPlaylists = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/playlists/user/${userId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setPlaylists(data.playlists || []);
      }
    } catch (err) {
      console.error('Error loading playlists:', err);
      setError('Error al cargar las listas de reproducción');
    } finally {
      setLoading(false);
    }
  };

  const createPlaylist = async () => {
    if (!playlistName.trim()) return;
    
    try {
      const newPlaylist: Playlist = {
        id: 'new-' + Date.now(),
        name: playlistName.trim(),
        description: playlistDescription.trim(),
        videos: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        is_public: isPublic,
        total_duration: 0,
        completed_videos: 0,
        tags: playlistTags.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0)
      };

      // In a real app, this would be an API call
      const response = await fetch('/api/v1/playlists', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(newPlaylist)
      });

      if (response.ok) {
        const savedPlaylist = await response.json();
        setPlaylists(prev => [...prev, savedPlaylist]);
        setShowCreateDialog(false);
        setPlaylistName('');
        setPlaylistDescription('');
        setPlaylistTags('');
        setIsPublic(false);
      }
    } catch (err) {
      console.error('Error creating playlist:', err);
      setError('Error al crear la lista de reproducción');
    }
  };

  const addVideoToPlaylist = async (video: VideoItem, playlistId: string) => {
    const playlist = playlists.find(p => p.id === playlistId);
    if (!playlist || playlist.videos.length >= maxPlaylistSize) return;

    const updatedPlaylist = {
      ...playlist,
      videos: [...playlist.videos, video],
      total_duration: playlist.total_duration + (video.duration_seconds || 0),
      updated_at: new Date().toISOString()
    };

    // Update local state
    setPlaylists(prev => prev.map(p => p.id === playlistId ? updatedPlaylist : p));
    
    // Update current playlist if it's the same
    if (currentPlaylist?.id === playlistId) {
      setCurrentPlaylist(updatedPlaylist);
    }

    // In a real app, sync with backend
    try {
      await fetch(`/api/v1/playlists/${playlistId}/videos`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ video_id: video.video_id })
      });
    } catch (err) {
      console.error('Error adding video to playlist:', err);
    }
  };

  const removeVideoFromPlaylist = async (videoIndex: number, playlistId: string) => {
    const playlist = playlists.find(p => p.id === playlistId);
    if (!playlist) return;

    const videoToRemove = playlist.videos[videoIndex];
    const updatedPlaylist = {
      ...playlist,
      videos: playlist.videos.filter((_, index) => index !== videoIndex),
      total_duration: playlist.total_duration - (videoToRemove.duration_seconds || 0),
      updated_at: new Date().toISOString()
    };

    setPlaylists(prev => prev.map(p => p.id === playlistId ? updatedPlaylist : p));
    
    if (currentPlaylist?.id === playlistId) {
      setCurrentPlaylist(updatedPlaylist);
      // Adjust current video index if necessary
      if (currentVideoIndex >= videoIndex && currentVideoIndex > 0) {
        setCurrentVideoIndex(currentVideoIndex - 1);
      }
    }
  };

  const playVideo = useCallback((video: VideoItem, videoIndex?: number) => {
    if (videoIndex !== undefined) {
      setCurrentVideoIndex(videoIndex);
    }
    setIsPlaying(true);
    if (onVideoSelect) {
      onVideoSelect(video, currentPlaylist || undefined);
    }
  }, [onVideoSelect, currentPlaylist]);

  const nextVideo = useCallback(() => {
    if (!currentPlaylist || currentPlaylist.videos.length === 0) return;

    let nextIndex = currentVideoIndex;
    
    if (playMode === 'shuffle') {
      nextIndex = Math.floor(Math.random() * currentPlaylist.videos.length);
    } else if (playMode === 'normal' || playMode === 'repeat') {
      nextIndex = currentVideoIndex + 1;
      if (nextIndex >= currentPlaylist.videos.length) {
        nextIndex = playMode === 'repeat' ? 0 : currentVideoIndex;
      }
    }

    if (nextIndex !== currentVideoIndex) {
      playVideo(currentPlaylist.videos[nextIndex], nextIndex);
    }
  }, [currentPlaylist, currentVideoIndex, playMode, playVideo]);

  const previousVideo = useCallback(() => {
    if (!currentPlaylist || currentPlaylist.videos.length === 0) return;

    let prevIndex = currentVideoIndex - 1;
    if (prevIndex < 0) {
      prevIndex = playMode === 'repeat' ? currentPlaylist.videos.length - 1 : 0;
    }

    if (prevIndex !== currentVideoIndex) {
      playVideo(currentPlaylist.videos[prevIndex], prevIndex);
    }
  }, [currentPlaylist, currentVideoIndex, playMode, playVideo]);

  const toggleFavorite = async (video: VideoItem) => {
    // Update local state
    if (currentPlaylist) {
      const updatedVideos = currentPlaylist.videos.map(v => 
        v.video_id === video.video_id ? { ...v, is_favorite: !v.is_favorite } : v
      );
      setCurrentPlaylist({ ...currentPlaylist, videos: updatedVideos });
    }

    // Sync with backend
    try {
      await fetch(`/api/v1/videos/${video.video_id}/favorite`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ is_favorite: !video.is_favorite })
      });
    } catch (err) {
      console.error('Error toggling favorite:', err);
    }
  };

  const toggleBookmark = async (video: VideoItem) => {
    // Update local state
    if (currentPlaylist) {
      const updatedVideos = currentPlaylist.videos.map(v => 
        v.video_id === video.video_id ? { ...v, is_bookmarked: !v.is_bookmarked } : v
      );
      setCurrentPlaylist({ ...currentPlaylist, videos: updatedVideos });
    }

    // Sync with backend
    try {
      await fetch(`/api/v1/videos/${video.video_id}/bookmark`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ is_bookmarked: !video.is_bookmarked })
      });
    } catch (err) {
      console.error('Error toggling bookmark:', err);
    }
  };

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getProgressColor = (percentage: number): string => {
    if (percentage >= 80) return 'bg-green-500';
    if (percentage >= 50) return 'bg-yellow-500';
    return 'bg-blue-500';
  };

  const filteredPlaylists = playlists.filter(playlist => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      if (!playlist.name.toLowerCase().includes(query) && 
          !playlist.description?.toLowerCase().includes(query) &&
          !playlist.tags.some(tag => tag.toLowerCase().includes(query))) {
        return false;
      }
    }

    if (filterSubject !== 'all' && playlist.subject_focus !== filterSubject) {
      return false;
    }

    if (filterLevel !== 'all' && playlist.difficulty_level !== filterLevel) {
      return false;
    }

    if (filterCompletion !== 'all') {
      const completionRate = playlist.videos.length > 0 ? 
        (playlist.completed_videos / playlist.videos.length) * 100 : 0;
      
      if (filterCompletion === 'completed' && completionRate < 80) return false;
      if (filterCompletion === 'in-progress' && (completionRate === 0 || completionRate >= 80)) return false;
      if (filterCompletion === 'not-started' && completionRate > 0) return false;
    }

    return true;
  });

  const currentVideo = currentPlaylist?.videos[currentVideoIndex];

  return (
    <div className="w-full space-y-6">
      {error && (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Playlist Controls */}
      {showControls && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <PlayCircle className="w-5 h-5" />
                {currentPlaylist?.name || 'Ninguna lista seleccionada'}
              </CardTitle>
              
              <div className="flex items-center gap-2">
                {allowCreatePlaylist && (
                  <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
                    <DialogTrigger asChild>
                      <Button variant="outline" size="sm">
                        <Plus className="w-4 h-4 mr-1" />
                        Nueva Lista
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Crear Nueva Lista de Reproducción</DialogTitle>
                        <DialogDescription>
                          Organiza tus videos en listas personalizadas para estudiar de manera más efectiva.
                        </DialogDescription>
                      </DialogHeader>
                      
                      <div className="space-y-4">
                        <Input
                          placeholder="Nombre de la lista"
                          value={playlistName}
                          onChange={(e) => setPlaylistName(e.target.value)}
                        />
                        
                        <Textarea
                          placeholder="Descripción (opcional)"
                          value={playlistDescription}
                          onChange={(e) => setPlaylistDescription(e.target.value)}
                          rows={3}
                        />
                        
                        <Input
                          placeholder="Etiquetas separadas por comas"
                          value={playlistTags}
                          onChange={(e) => setPlaylistTags(e.target.value)}
                        />
                        
                        <div className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            id="public"
                            checked={isPublic}
                            onChange={(e) => setIsPublic(e.target.checked)}
                          />
                          <label htmlFor="public" className="text-sm">
                            Hacer pública esta lista
                          </label>
                        </div>
                        
                        <div className="flex justify-end gap-2">
                          <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                            Cancelar
                          </Button>
                          <Button onClick={createPlaylist} disabled={!playlistName.trim()}>
                            Crear Lista
                          </Button>
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>
                )}
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setViewMode(viewMode === 'list' ? 'grid' : 'list')}
                >
                  {viewMode === 'list' ? <Grid className="w-4 h-4" /> : <List className="w-4 h-4" />}
                </Button>
              </div>
            </div>
          </CardHeader>
          
          <CardContent>
            {/* Playback Controls */}
            {currentPlaylist && currentVideo && (
              <div className="flex items-center justify-between mb-4 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-4">
                  <img 
                    src={currentVideo.thumbnail_url || `https://img.youtube.com/vi/${currentVideo.youtube_id}/mqdefault.jpg`}
                    alt={currentVideo.title}
                    className="w-16 h-12 object-cover rounded"
                  />
                  
                  <div>
                    <h4 className="font-medium text-sm line-clamp-1">{currentVideo.title}</h4>
                    <p className="text-xs text-gray-600">{currentVideo.channel}</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={previousVideo}
                    disabled={currentPlaylist.videos.length <= 1}
                  >
                    <SkipBack className="w-4 h-4" />
                  </Button>
                  
                  <Button
                    size="sm"
                    onClick={() => setIsPlaying(!isPlaying)}
                  >
                    {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </Button>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={nextVideo}
                    disabled={currentPlaylist.videos.length <= 1}
                  >
                    <SkipForward className="w-4 h-4" />
                  </Button>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setPlayMode(playMode === 'normal' ? 'shuffle' : playMode === 'shuffle' ? 'repeat' : 'normal')}
                  >
                    {playMode === 'shuffle' ? <Shuffle className="w-4 h-4" /> : 
                     playMode === 'repeat' ? <Repeat className="w-4 h-4" /> : 
                     <Play className="w-4 h-4" />}
                  </Button>
                </div>
              </div>
            )}
            
            {/* Playlist Stats */}
            {currentPlaylist && (
              <div className="grid grid-cols-4 gap-4 mb-4">
                <div className="text-center">
                  <div className="text-lg font-bold">{currentPlaylist.videos.length}</div>
                  <div className="text-xs text-gray-600">Videos</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold">{formatDuration(currentPlaylist.total_duration)}</div>
                  <div className="text-xs text-gray-600">Duración</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold">{currentPlaylist.completed_videos}</div>
                  <div className="text-xs text-gray-600">Completados</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold">
                    {currentPlaylist.videos.length > 0 ? 
                      Math.round((currentPlaylist.completed_videos / currentPlaylist.videos.length) * 100) : 0}%
                  </div>
                  <div className="text-xs text-gray-600">Progreso</div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tabs for Playlists and Current Playlist */}
      <Tabs defaultValue="current" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="current">Lista Actual</TabsTrigger>
          <TabsTrigger value="playlists">Mis Listas</TabsTrigger>
        </TabsList>
        
        <TabsContent value="current" className="space-y-4">
          {currentPlaylist ? (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">{currentPlaylist.name}</CardTitle>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">
                      {currentPlaylist.videos.length} videos
                    </Badge>
                    {currentPlaylist.tags.map(tag => (
                      <Badge key={tag} variant="outline" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
                {currentPlaylist.description && (
                  <p className="text-sm text-gray-600">{currentPlaylist.description}</p>
                )}
              </CardHeader>
              
              <CardContent>
                <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4' : 'space-y-3'}>
                  {currentPlaylist.videos.map((video, index) => (
                    <Card 
                      key={video.video_id} 
                      className={`group cursor-pointer transition-all duration-200 ${
                        index === currentVideoIndex ? 'ring-2 ring-blue-500 bg-blue-50' : 'hover:shadow-md'
                      }`}
                      onClick={() => playVideo(video, index)}
                    >
                      <CardContent className={viewMode === 'grid' ? 'p-4' : 'p-3'}>
                        <div className={viewMode === 'grid' ? 'space-y-3' : 'flex gap-3'}>
                          {/* Thumbnail */}
                          <div className={`relative ${viewMode === 'grid' ? 'w-full' : 'flex-shrink-0'}`}>
                            <img 
                              src={video.thumbnail_url || `https://img.youtube.com/vi/${video.youtube_id}/mqdefault.jpg`}
                              alt={video.title}
                              className={`${viewMode === 'grid' ? 'w-full h-32' : 'w-32 h-20'} object-cover rounded`}
                            />
                            
                            {/* Progress overlay */}
                            {video.watched_percentage && video.watched_percentage > 0 && (
                              <div className="absolute bottom-0 left-0 right-0 h-1">
                                <div 
                                  className={`h-full ${getProgressColor(video.watched_percentage)}`}
                                  style={{ width: `${Math.min(video.watched_percentage, 100)}%` }}
                                />
                              </div>
                            )}
                            
                            {/* Play overlay */}
                            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 rounded flex items-center justify-center transition-all duration-200">
                              {index === currentVideoIndex && isPlaying ? (
                                <Pause className="w-8 h-8 text-white opacity-0 group-hover:opacity-100" />
                              ) : (
                                <Play className="w-8 h-8 text-white opacity-0 group-hover:opacity-100" />
                              )}
                            </div>
                            
                            {/* Duration badge */}
                            {video.duration_seconds && (
                              <Badge className="absolute bottom-1 right-1 text-xs">
                                {formatDuration(video.duration_seconds)}
                              </Badge>
                            )}
                          </div>
                          
                          {/* Video info */}
                          <div className="flex-1 space-y-2">
                            <div className="flex items-start justify-between">
                              <h4 className="font-medium text-sm line-clamp-2 group-hover:text-blue-600">
                                {video.title}
                              </h4>
                              
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                                    <MoreVertical className="w-3 h-3" />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                  <DropdownMenuItem onClick={(e) => {
                                    e.stopPropagation();
                                    toggleFavorite(video);
                                  }}>
                                    {video.is_favorite ? (
                                      <>
                                        <HeartOff className="w-4 h-4 mr-2" />
                                        Quitar de favoritos
                                      </>
                                    ) : (
                                      <>
                                        <Heart className="w-4 h-4 mr-2" />
                                        Agregar a favoritos
                                      </>
                                    )}
                                  </DropdownMenuItem>
                                  <DropdownMenuItem onClick={(e) => {
                                    e.stopPropagation();
                                    toggleBookmark(video);
                                  }}>
                                    {video.is_bookmarked ? (
                                      <>
                                        <Bookmark className="w-4 h-4 mr-2" />
                                        Quitar marcador
                                      </>
                                    ) : (
                                      <>
                                        <BookmarkPlus className="w-4 h-4 mr-2" />
                                        Marcar para después
                                      </>
                                    )}
                                  </DropdownMenuItem>
                                  <DropdownMenuSeparator />
                                  <DropdownMenuItem onClick={(e) => {
                                    e.stopPropagation();
                                    window.open(video.url, '_blank');
                                  }}>
                                    <ExternalLink className="w-4 h-4 mr-2" />
                                    Abrir en YouTube
                                  </DropdownMenuItem>
                                  <DropdownMenuSeparator />
                                  <DropdownMenuItem
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      removeVideoFromPlaylist(index, currentPlaylist.id);
                                    }}
                                    className="text-red-600"
                                  >
                                    <Trash2 className="w-4 h-4 mr-2" />
                                    Quitar de la lista
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
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
                            
                            <div className="flex flex-wrap gap-1">
                              <Badge variant="outline" className="text-xs">
                                <Star className="w-3 h-3 mr-1" />
                                {Math.round(video.scores.total_score * 100)}%
                              </Badge>
                              
                              {video.watched_percentage && video.watched_percentage > 0 && (
                                <Badge variant="secondary" className="text-xs">
                                  <Eye className="w-3 h-3 mr-1" />
                                  {Math.round(video.watched_percentage)}%
                                </Badge>
                              )}
                              
                              {video.is_favorite && (
                                <Badge variant="outline" className="text-xs text-red-500">
                                  <Heart className="w-3 h-3" />
                                </Badge>
                              )}
                              
                              {video.is_bookmarked && (
                                <Badge variant="outline" className="text-xs text-blue-500">
                                  <Bookmark className="w-3 h-3" />
                                </Badge>
                              )}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
                
                {currentPlaylist.videos.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <PlayCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>Esta lista de reproducción está vacía</p>
                    <p className="text-sm">Agrega videos para empezar a aprender</p>
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="text-center py-8">
                <List className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-600 mb-2">No hay lista seleccionada</p>
                <p className="text-sm text-gray-500">Selecciona una lista de reproducción para comenzar</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
        
        <TabsContent value="playlists" className="space-y-4">
          {/* Search and filters */}
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <Input
                      placeholder="Buscar listas de reproducción..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>
                
                <div className="flex gap-2">
                  <select
                    value={filterSubject}
                    onChange={(e) => setFilterSubject(e.target.value)}
                    className="text-sm border rounded px-3 py-2"
                  >
                    <option value="all">Todas las materias</option>
                    <option value="matemáticas">Matemáticas</option>
                    <option value="lenguaje">Lenguaje</option>
                    <option value="ciencias">Ciencias</option>
                    <option value="sociales">Sociales</option>
                    <option value="inglés">Inglés</option>
                  </select>
                  
                  <select
                    value={filterCompletion}
                    onChange={(e) => setFilterCompletion(e.target.value)}
                    className="text-sm border rounded px-3 py-2"
                  >
                    <option value="all">Todos los estados</option>
                    <option value="completed">Completadas</option>
                    <option value="in-progress">En progreso</option>
                    <option value="not-started">No iniciadas</option>
                  </select>
                </div>
              </div>
            </CardContent>
          </Card>
          
          {/* Playlists grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredPlaylists.map(playlist => {
              const completionRate = playlist.videos.length > 0 ? 
                (playlist.completed_videos / playlist.videos.length) * 100 : 0;
              
              return (
                <Card 
                  key={playlist.id}
                  className="group cursor-pointer hover:shadow-lg transition-all duration-200"
                  onClick={() => setCurrentPlaylist(playlist)}
                >
                  <CardContent className="p-4">
                    <div className="space-y-3">
                      {/* Playlist thumbnail grid */}
                      <div className="grid grid-cols-2 gap-1 h-24 rounded overflow-hidden">
                        {playlist.videos.slice(0, 4).map((video, index) => (
                          <img
                            key={index}
                            src={video.thumbnail_url || `https://img.youtube.com/vi/${video.youtube_id}/mqdefault.jpg`}
                            alt=""
                            className="w-full h-full object-cover"
                          />
                        ))}
                        {playlist.videos.length === 0 && (
                          <div className="col-span-2 flex items-center justify-center bg-gray-100 h-full">
                            <PlayCircle className="w-8 h-8 text-gray-400" />
                          </div>
                        )}
                      </div>
                      
                      {/* Playlist info */}
                      <div>
                        <h3 className="font-semibold text-sm group-hover:text-blue-600 line-clamp-2">
                          {playlist.name}
                        </h3>
                        {playlist.description && (
                          <p className="text-xs text-gray-600 line-clamp-2 mt-1">
                            {playlist.description}
                          </p>
                        )}
                      </div>
                      
                      {/* Stats */}
                      <div className="flex justify-between items-center text-xs text-gray-600">
                        <span>{playlist.videos.length} videos</span>
                        <span>{formatDuration(playlist.total_duration)}</span>
                      </div>
                      
                      {/* Progress bar */}
                      {playlist.videos.length > 0 && (
                        <div>
                          <div className="flex justify-between items-center text-xs mb-1">
                            <span>Progreso</span>
                            <span>{Math.round(completionRate)}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className={`h-2 rounded-full ${getProgressColor(completionRate)}`}
                              style={{ width: `${Math.min(completionRate, 100)}%` }}
                            />
                          </div>
                        </div>
                      )}
                      
                      {/* Tags */}
                      {playlist.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {playlist.tags.slice(0, 3).map(tag => (
                            <Badge key={tag} variant="outline" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                          {playlist.tags.length > 3 && (
                            <Badge variant="outline" className="text-xs">
                              +{playlist.tags.length - 3}
                            </Badge>
                          )}
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
          
          {filteredPlaylists.length === 0 && (
            <Card>
              <CardContent className="text-center py-8">
                <List className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-600 mb-2">
                  {searchQuery ? 'No se encontraron listas de reproducción' : 'No tienes listas de reproducción'}
                </p>
                <p className="text-sm text-gray-500">
                  {searchQuery ? 'Prueba con otros términos de búsqueda' : 'Crea tu primera lista para organizar tus videos de estudio'}
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}