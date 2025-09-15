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
  Bookmark,
  BookmarkPlus,
  BookmarkCheck,
  BookmarkX,
  Play,
  Clock,
  Calendar,
  Tag,
  Star,
  Eye,
  Filter,
  Search,
  Sort,
  Grid,
  List,
  MoreVertical,
  Edit,
  Trash2,
  Share2,
  Download,
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  Info,
  TrendingUp,
  Target,
  BookOpen,
  Zap,
  Timer,
  BarChart,
  PieChart,
  Activity,
  MapPin,
  Flag,
  MessageSquare,
  Hash,
  Users
} from 'lucide-react';

interface VideoBookmark {
  id: string;
  video_id: number;
  youtube_id: string;
  title: string;
  channel: string;
  thumbnail_url?: string;
  url: string;
  duration_seconds?: number;
  
  // Bookmark specific data
  bookmark_timestamp: number; // seconds into the video
  bookmark_note?: string;
  bookmark_tags: string[];
  bookmark_category: 'learning' | 'review' | 'practice' | 'concept' | 'example' | 'exercise';
  priority_level: 'low' | 'medium' | 'high' | 'urgent';
  
  // Progress tracking
  watch_progress: {
    watched_seconds: number;
    total_duration: number;
    completion_percentage: number;
    last_position: number; // last watched position in seconds
    watch_sessions: number;
    total_watch_time: number;
    first_watched: string;
    last_watched: string;
  };
  
  // Learning analytics
  learning_metrics: {
    difficulty_rating: number; // 1-5
    usefulness_rating: number; // 1-5
    comprehension_level: number; // 1-5
    times_reviewed: number;
    concepts_learned: string[];
    skills_improved: string[];
    questions_answered: number;
    performance_improvement: number;
  };
  
  // Context information
  context: {
    subject_area?: string;
    topic?: string;
    study_session_id?: string;
    related_question_ids: string[];
    recommendation_reason?: string;
    added_from: 'recommendation' | 'search' | 'manual' | 'study_plan';
  };
  
  // Metadata
  created_at: string;
  updated_at: string;
  is_favorite: boolean;
  is_archived: boolean;
}

interface StudySession {
  id: string;
  name: string;
  description?: string;
  bookmarks: VideoBookmark[];
  total_study_time: number;
  completion_rate: number;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  goals: string[];
  progress_milestones: {
    milestone: string;
    completed: boolean;
    completed_at?: string;
  }[];
}

interface VideoBookmarkSystemProps {
  userId: string;
  currentVideo?: {
    video_id: number;
    youtube_id: string;
    title: string;
    current_timestamp?: number;
  };
  onBookmarkSelect?: (bookmark: VideoBookmark) => void;
  onProgressUpdate?: (videoId: number, progress: any) => void;
  showAnalytics?: boolean;
  allowSessions?: boolean;
  maxBookmarksPerCategory?: number;
}

export default function VideoBookmarkSystem({
  userId,
  currentVideo,
  onBookmarkSelect,
  onProgressUpdate,
  showAnalytics = true,
  allowSessions = true,
  maxBookmarksPerCategory = 25
}: VideoBookmarkSystemProps) {
  // State management
  const [bookmarks, setBookmarks] = useState<VideoBookmark[]>([]);
  const [sessions, setSessions] = useState<StudySession[]>([]);
  const [currentSession, setCurrentSession] = useState<StudySession | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // View and filter state
  const [viewMode, setViewMode] = useState<'list' | 'grid' | 'timeline'>('list');
  const [sortBy, setSortBy] = useState<'date' | 'priority' | 'progress' | 'rating'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [filterPriority, setFilterPriority] = useState<string>('all');
  const [filterCompletion, setFilterCompletion] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Form states
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [bookmarkNote, setBookmarkNote] = useState('');
  const [bookmarkTags, setBookmarkTags] = useState('');
  const [bookmarkCategory, setBookmarkCategory] = useState<VideoBookmark['bookmark_category']>('learning');
  const [priorityLevel, setPriorityLevel] = useState<VideoBookmark['priority_level']>('medium');
  const [bookmarkTimestamp, setBookmarkTimestamp] = useState(0);

  // Load user bookmarks and sessions
  useEffect(() => {
    loadBookmarks();
    if (allowSessions) {
      loadStudySessions();
    }
  }, [userId]);

  const loadBookmarks = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/bookmarks/user/${userId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setBookmarks(data.bookmarks || []);
      }
    } catch (err) {
      console.error('Error loading bookmarks:', err);
      setError('Error al cargar los marcadores');
    } finally {
      setLoading(false);
    }
  };

  const loadStudySessions = async () => {
    try {
      const response = await fetch(`/api/v1/study-sessions/user/${userId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSessions(data.sessions || []);
        
        // Set active session if exists
        const activeSession = data.sessions?.find((s: StudySession) => s.is_active);
        if (activeSession) {
          setCurrentSession(activeSession);
        }
      }
    } catch (err) {
      console.error('Error loading study sessions:', err);
    }
  };

  const createBookmark = async () => {
    if (!currentVideo) return;

    const newBookmark: Partial<VideoBookmark> = {
      video_id: currentVideo.video_id,
      youtube_id: currentVideo.youtube_id,
      title: currentVideo.title,
      bookmark_timestamp: currentVideo.current_timestamp || bookmarkTimestamp,
      bookmark_note: bookmarkNote.trim(),
      bookmark_tags: bookmarkTags.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0),
      bookmark_category: bookmarkCategory,
      priority_level: priorityLevel,
      context: {
        added_from: 'manual',
        related_question_ids: []
      },
      learning_metrics: {
        difficulty_rating: 3,
        usefulness_rating: 3,
        comprehension_level: 3,
        times_reviewed: 0,
        concepts_learned: [],
        skills_improved: [],
        questions_answered: 0,
        performance_improvement: 0
      }
    };

    try {
      const response = await fetch('/api/v1/bookmarks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(newBookmark)
      });

      if (response.ok) {
        const savedBookmark = await response.json();
        setBookmarks(prev => [savedBookmark, ...prev]);
        
        // Add to current session if active
        if (currentSession) {
          addBookmarkToSession(savedBookmark.id, currentSession.id);
        }
        
        // Reset form
        setShowAddDialog(false);
        setBookmarkNote('');
        setBookmarkTags('');
        setBookmarkCategory('learning');
        setPriorityLevel('medium');
      }
    } catch (err) {
      console.error('Error creating bookmark:', err);
      setError('Error al crear el marcador');
    }
  };

  const updateBookmarkProgress = async (bookmarkId: string, progressData: any) => {
    try {
      const response = await fetch(`/api/v1/bookmarks/${bookmarkId}/progress`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(progressData)
      });

      if (response.ok) {
        const updatedBookmark = await response.json();
        setBookmarks(prev => prev.map(b => b.id === bookmarkId ? updatedBookmark : b));
        
        if (onProgressUpdate) {
          onProgressUpdate(updatedBookmark.video_id, progressData);
        }
      }
    } catch (err) {
      console.error('Error updating progress:', err);
    }
  };

  const addBookmarkToSession = async (bookmarkId: string, sessionId: string) => {
    try {
      await fetch(`/api/v1/study-sessions/${sessionId}/bookmarks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ bookmark_id: bookmarkId })
      });
      
      // Reload sessions to get updated data
      loadStudySessions();
    } catch (err) {
      console.error('Error adding bookmark to session:', err);
    }
  };

  const rateBookmark = async (bookmarkId: string, ratings: Partial<VideoBookmark['learning_metrics']>) => {
    const bookmark = bookmarks.find(b => b.id === bookmarkId);
    if (!bookmark) return;

    const updatedMetrics = {
      ...bookmark.learning_metrics,
      ...ratings
    };

    try {
      const response = await fetch(`/api/v1/bookmarks/${bookmarkId}/rating`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ learning_metrics: updatedMetrics })
      });

      if (response.ok) {
        const updatedBookmark = await response.json();
        setBookmarks(prev => prev.map(b => b.id === bookmarkId ? updatedBookmark : b));
      }
    } catch (err) {
      console.error('Error rating bookmark:', err);
    }
  };

  const deleteBookmark = async (bookmarkId: string) => {
    try {
      await fetch(`/api/v1/bookmarks/${bookmarkId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      setBookmarks(prev => prev.filter(b => b.id !== bookmarkId));
    } catch (err) {
      console.error('Error deleting bookmark:', err);
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

  const formatTimestamp = (seconds: number): string => {
    return formatDuration(seconds);
  };

  const getCategoryIcon = (category: VideoBookmark['bookmark_category']) => {
    switch (category) {
      case 'learning': return <BookOpen className="w-4 h-4" />;
      case 'review': return <Eye className="w-4 h-4" />;
      case 'practice': return <Target className="w-4 h-4" />;
      case 'concept': return <Zap className="w-4 h-4" />;
      case 'example': return <Star className="w-4 h-4" />;
      case 'exercise': return <TrendingUp className="w-4 h-4" />;
      default: return <Bookmark className="w-4 h-4" />;
    }
  };

  const getPriorityColor = (priority: VideoBookmark['priority_level']) => {
    switch (priority) {
      case 'urgent': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  const getProgressColor = (percentage: number): string => {
    if (percentage >= 90) return 'bg-green-500';
    if (percentage >= 70) return 'bg-blue-500';
    if (percentage >= 40) return 'bg-yellow-500';
    return 'bg-gray-500';
  };

  const sortedAndFilteredBookmarks = bookmarks
    .filter(bookmark => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        if (!bookmark.title.toLowerCase().includes(query) &&
            !bookmark.bookmark_note?.toLowerCase().includes(query) &&
            !bookmark.bookmark_tags.some(tag => tag.toLowerCase().includes(query))) {
          return false;
        }
      }

      // Category filter
      if (filterCategory !== 'all' && bookmark.bookmark_category !== filterCategory) {
        return false;
      }

      // Priority filter
      if (filterPriority !== 'all' && bookmark.priority_level !== filterPriority) {
        return false;
      }

      // Completion filter
      if (filterCompletion !== 'all') {
        const completion = bookmark.watch_progress.completion_percentage;
        if (filterCompletion === 'completed' && completion < 90) return false;
        if (filterCompletion === 'in-progress' && (completion === 0 || completion >= 90)) return false;
        if (filterCompletion === 'not-started' && completion > 0) return false;
      }

      return true;
    })
    .sort((a, b) => {
      let comparison = 0;

      switch (sortBy) {
        case 'date':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
        case 'priority':
          const priorityOrder = { urgent: 4, high: 3, medium: 2, low: 1 };
          comparison = priorityOrder[a.priority_level] - priorityOrder[b.priority_level];
          break;
        case 'progress':
          comparison = a.watch_progress.completion_percentage - b.watch_progress.completion_percentage;
          break;
        case 'rating':
          comparison = a.learning_metrics.usefulness_rating - b.learning_metrics.usefulness_rating;
          break;
        default:
          comparison = 0;
      }

      return sortOrder === 'desc' ? -comparison : comparison;
    });

  const renderBookmarkCard = (bookmark: VideoBookmark) => (
    <Card 
      key={bookmark.id}
      className="group cursor-pointer hover:shadow-lg transition-all duration-200"
      onClick={() => onBookmarkSelect && onBookmarkSelect(bookmark)}
    >
      <CardContent className="p-4">
        <div className={viewMode === 'grid' ? 'space-y-3' : 'flex gap-4'}>
          {/* Thumbnail */}
          <div className={`relative ${viewMode === 'grid' ? 'w-full' : 'flex-shrink-0'}`}>
            <img 
              src={bookmark.thumbnail_url || `https://img.youtube.com/vi/${bookmark.youtube_id}/mqdefault.jpg`}
              alt={bookmark.title}
              className={`${viewMode === 'grid' ? 'w-full h-32' : 'w-32 h-20'} object-cover rounded`}
            />
            
            {/* Progress overlay */}
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200 rounded-b">
              <div 
                className={`h-full ${getProgressColor(bookmark.watch_progress.completion_percentage)} rounded-b`}
                style={{ width: `${bookmark.watch_progress.completion_percentage}%` }}
              />
            </div>
            
            {/* Bookmark timestamp indicator */}
            <Badge className="absolute top-1 right-1 text-xs bg-blue-600">
              <MapPin className="w-3 h-3 mr-1" />
              {formatTimestamp(bookmark.bookmark_timestamp)}
            </Badge>
            
            {/* Priority indicator */}
            <div className={`absolute top-1 left-1 w-3 h-3 rounded-full ${getPriorityColor(bookmark.priority_level)}`} />
          </div>
          
          {/* Bookmark info */}
          <div className="flex-1 space-y-2">
            <div className="flex items-start justify-between">
              <div>
                <h4 className="font-medium text-sm line-clamp-2 group-hover:text-blue-600">
                  {bookmark.title}
                </h4>
                <p className="text-xs text-gray-600">{bookmark.channel}</p>
              </div>
              
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                    <MoreVertical className="w-3 h-3" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={(e) => {
                    e.stopPropagation();
                    // Edit bookmark logic
                  }}>
                    <Edit className="w-4 h-4 mr-2" />
                    Editar marcador
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={(e) => {
                    e.stopPropagation();
                    // Add to session logic
                  }}>
                    <BookmarkPlus className="w-4 h-4 mr-2" />
                    Agregar a sesión
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={(e) => {
                    e.stopPropagation();
                    window.open(bookmark.url, '_blank');
                  }}>
                    <ExternalLink className="w-4 h-4 mr-2" />
                    Abrir en YouTube
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteBookmark(bookmark.id);
                    }}
                    className="text-red-600"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Eliminar
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
            
            {/* Bookmark note */}
            {bookmark.bookmark_note && (
              <p className="text-xs text-gray-700 bg-yellow-50 p-2 rounded italic">
                "{bookmark.bookmark_note}"
              </p>
            )}
            
            {/* Tags and category */}
            <div className="flex flex-wrap gap-1">
              <Badge variant="outline" className="text-xs">
                {getCategoryIcon(bookmark.bookmark_category)}
                <span className="ml-1 capitalize">{bookmark.bookmark_category}</span>
              </Badge>
              
              {bookmark.bookmark_tags.slice(0, 3).map(tag => (
                <Badge key={tag} variant="secondary" className="text-xs">
                  <Hash className="w-3 h-3 mr-1" />
                  {tag}
                </Badge>
              ))}
              
              {bookmark.bookmark_tags.length > 3 && (
                <Badge variant="secondary" className="text-xs">
                  +{bookmark.bookmark_tags.length - 3}
                </Badge>
              )}
            </div>
            
            {/* Progress and ratings */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex items-center gap-1">
                <Activity className="w-3 h-3" />
                <span>{Math.round(bookmark.watch_progress.completion_percentage)}% visto</span>
              </div>
              <div className="flex items-center gap-1">
                <Star className="w-3 h-3" />
                <span>{bookmark.learning_metrics.usefulness_rating}/5</span>
              </div>
              <div className="flex items-center gap-1">
                <Timer className="w-3 h-3" />
                <span>{formatDuration(bookmark.watch_progress.watched_seconds)}</span>
              </div>
              <div className="flex items-center gap-1">
                <Eye className="w-3 h-3" />
                <span>{bookmark.watch_progress.watch_sessions}x</span>
              </div>
            </div>
            
            {/* Learning metrics */}
            {showAnalytics && (
              <div className="flex items-center gap-2 text-xs text-gray-600">
                <div className="flex items-center gap-1">
                  <BarChart className="w-3 h-3" />
                  <span>Dificultad: {bookmark.learning_metrics.difficulty_rating}/5</span>
                </div>
                <div className="flex items-center gap-1">
                  <TrendingUp className="w-3 h-3" />
                  <span>Comprensión: {bookmark.learning_metrics.comprehension_level}/5</span>
                </div>
              </div>
            )}
            
            {/* Context info */}
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>Agregado: {new Date(bookmark.created_at).toLocaleDateString()}</span>
              {bookmark.context.subject_area && (
                <Badge variant="outline" className="text-xs">
                  {bookmark.context.subject_area}
                </Badge>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="w-full space-y-6">
      {error && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Header with controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Bookmark className="w-5 h-5" />
              Mis Marcadores de Video ({bookmarks.length})
            </CardTitle>
            
            <div className="flex items-center gap-2">
              {/* Add bookmark button */}
              {currentVideo && (
                <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
                  <DialogTrigger asChild>
                    <Button size="sm">
                      <BookmarkPlus className="w-4 h-4 mr-1" />
                      Marcar Video
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Crear Marcador de Video</DialogTitle>
                      <DialogDescription>
                        Guarda este momento del video para revisarlo más tarde
                      </DialogDescription>
                    </DialogHeader>
                    
                    <div className="space-y-4">
                      <div>
                        <label className="text-sm font-medium">Posición en el video</label>
                        <Input
                          type="number"
                          placeholder="Segundos"
                          value={bookmarkTimestamp}
                          onChange={(e) => setBookmarkTimestamp(parseInt(e.target.value) || 0)}
                        />
                      </div>
                      
                      <div>
                        <label className="text-sm font-medium">Nota (opcional)</label>
                        <Textarea
                          placeholder="¿Qué es importante recordar de este momento?"
                          value={bookmarkNote}
                          onChange={(e) => setBookmarkNote(e.target.value)}
                          rows={3}
                        />
                      </div>
                      
                      <div>
                        <label className="text-sm font-medium">Categoría</label>
                        <select
                          value={bookmarkCategory}
                          onChange={(e) => setBookmarkCategory(e.target.value as VideoBookmark['bookmark_category'])}
                          className="w-full text-sm border rounded px-3 py-2"
                        >
                          <option value="learning">Aprendizaje</option>
                          <option value="review">Repaso</option>
                          <option value="practice">Práctica</option>
                          <option value="concept">Concepto clave</option>
                          <option value="example">Ejemplo</option>
                          <option value="exercise">Ejercicio</option>
                        </select>
                      </div>
                      
                      <div>
                        <label className="text-sm font-medium">Prioridad</label>
                        <select
                          value={priorityLevel}
                          onChange={(e) => setPriorityLevel(e.target.value as VideoBookmark['priority_level'])}
                          className="w-full text-sm border rounded px-3 py-2"
                        >
                          <option value="low">Baja</option>
                          <option value="medium">Media</option>
                          <option value="high">Alta</option>
                          <option value="urgent">Urgente</option>
                        </select>
                      </div>
                      
                      <div>
                        <label className="text-sm font-medium">Etiquetas</label>
                        <Input
                          placeholder="Etiquetas separadas por comas"
                          value={bookmarkTags}
                          onChange={(e) => setBookmarkTags(e.target.value)}
                        />
                      </div>
                      
                      <div className="flex justify-end gap-2">
                        <Button variant="outline" onClick={() => setShowAddDialog(false)}>
                          Cancelar
                        </Button>
                        <Button onClick={createBookmark}>
                          Crear Marcador
                        </Button>
                      </div>
                    </div>
                  </DialogContent>
                </Dialog>
              )}
              
              {/* View mode toggle */}
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
          {/* Filters and search */}
          <div className="flex flex-col md:flex-row gap-4 mb-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <Input
                  placeholder="Buscar marcadores..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <div className="flex gap-2">
              <select
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
                className="text-sm border rounded px-3 py-2"
              >
                <option value="all">Todas las categorías</option>
                <option value="learning">Aprendizaje</option>
                <option value="review">Repaso</option>
                <option value="practice">Práctica</option>
                <option value="concept">Concepto</option>
                <option value="example">Ejemplo</option>
                <option value="exercise">Ejercicio</option>
              </select>
              
              <select
                value={filterPriority}
                onChange={(e) => setFilterPriority(e.target.value)}
                className="text-sm border rounded px-3 py-2"
              >
                <option value="all">Todas las prioridades</option>
                <option value="urgent">Urgente</option>
                <option value="high">Alta</option>
                <option value="medium">Media</option>
                <option value="low">Baja</option>
              </select>
              
              <select
                value={filterCompletion}
                onChange={(e) => setFilterCompletion(e.target.value)}
                className="text-sm border rounded px-3 py-2"
              >
                <option value="all">Todo el progreso</option>
                <option value="completed">Completados</option>
                <option value="in-progress">En progreso</option>
                <option value="not-started">No iniciados</option>
              </select>
              
              <select
                value={`${sortBy}-${sortOrder}`}
                onChange={(e) => {
                  const [sort, order] = e.target.value.split('-');
                  setSortBy(sort as typeof sortBy);
                  setSortOrder(order as typeof sortOrder);
                }}
                className="text-sm border rounded px-3 py-2"
              >
                <option value="date-desc">Más recientes</option>
                <option value="date-asc">Más antiguos</option>
                <option value="priority-desc">Mayor prioridad</option>
                <option value="progress-asc">Menos progreso</option>
                <option value="progress-desc">Más progreso</option>
                <option value="rating-desc">Mejor valorados</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Bookmarks list */}
      <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4' : 'space-y-3'}>
        {sortedAndFilteredBookmarks.map(renderBookmarkCard)}
      </div>
      
      {sortedAndFilteredBookmarks.length === 0 && (
        <Card>
          <CardContent className="text-center py-8">
            <Bookmark className="w-12 h-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600 mb-2">
              {searchQuery || filterCategory !== 'all' || filterPriority !== 'all' || filterCompletion !== 'all'
                ? 'No se encontraron marcadores con los filtros aplicados'
                : 'No tienes marcadores de video todavía'}
            </p>
            <p className="text-sm text-gray-500">
              {searchQuery || filterCategory !== 'all' || filterPriority !== 'all' || filterCompletion !== 'all'
                ? 'Prueba ajustando los filtros de búsqueda'
                : 'Comienza marcando momentos importantes de los videos mientras estudias'}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Analytics summary */}
      {showAnalytics && bookmarks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart className="w-5 h-5" />
              Resumen de Aprendizaje
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {bookmarks.filter(b => b.watch_progress.completion_percentage >= 90).length}
                </div>
                <div className="text-sm text-gray-600">Videos Completados</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {Math.round(
                    bookmarks.reduce((sum, b) => sum + b.learning_metrics.usefulness_rating, 0) / bookmarks.length
                  * 10) / 10}
                </div>
                <div className="text-sm text-gray-600">Utilidad Promedio</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {formatDuration(
                    bookmarks.reduce((sum, b) => sum + b.watch_progress.total_watch_time, 0)
                  )}
                </div>
                <div className="text-sm text-gray-600">Tiempo Total</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {bookmarks.reduce((sum, b) => sum + b.learning_metrics.concepts_learned.length, 0)}
                </div>
                <div className="text-sm text-gray-600">Conceptos Aprendidos</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}