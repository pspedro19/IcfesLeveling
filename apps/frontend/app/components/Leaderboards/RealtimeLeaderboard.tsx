'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Trophy, 
  TrendingUp, 
  TrendingDown,
  Medal,
  Crown,
  Star,
  Zap,
  Timer,
  Filter,
  Search,
  ChevronUp,
  ChevronDown,
  Sparkles
} from 'lucide-react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useAuthStore } from '@/stores/useAuthStore';
import { useAudio } from '../PortalLogin/AudioEngine';

interface LeaderboardEntry {
  rank: number;
  previousRank?: number;
  userId: string;
  username: string;
  avatar?: string;
  level: number;
  score: number;
  accuracy: number;
  questionsAnswered: number;
  streakDays: number;
  guildName?: string;
  heroClass: string;
  rankChange?: 'up' | 'down' | 'same' | 'new';
  isOnline?: boolean;
}

interface RealtimeLeaderboardProps {
  category?: 'global' | 'weekly' | 'daily' | 'guild';
  subject?: string;
  limit?: number;
}

export default function RealtimeLeaderboard({ 
  category = 'global',
  subject = 'all',
  limit = 50
}: RealtimeLeaderboardProps) {
  const { user } = useAuthStore();
  const { playSound } = useAudio();
  const { socket, isConnected, on } = useWebSocket();
  
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [filteredEntries, setFilteredEntries] = useState<LeaderboardEntry[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState(category);
  const [selectedSubject, setSelectedSubject] = useState(subject);
  const [isLoading, setIsLoading] = useState(true);
  const [userRank, setUserRank] = useState<number | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [newEntries, setNewEntries] = useState<Set<string>>(new Set());
  
  const scrollRef = useRef<HTMLDivElement>(null);
  
  // Categories and subjects
  const categories = [
    { value: 'global', label: 'Global', icon: '🌍' },
    { value: 'weekly', label: 'Semanal', icon: '📅' },
    { value: 'daily', label: 'Diario', icon: '☀️' },
    { value: 'guild', label: 'Gremio', icon: '⚔️' }
  ];
  
  const subjects = [
    { value: 'all', label: 'Todas las Materias' },
    { value: 'math', label: 'Matemáticas' },
    { value: 'reading', label: 'Lectura Crítica' },
    { value: 'science', label: 'Ciencias' },
    { value: 'social', label: 'Sociales' },
    { value: 'english', label: 'Inglés' }
  ];
  
  // Load initial leaderboard data
  useEffect(() => {
    fetchLeaderboard();
  }, [selectedCategory, selectedSubject]);
  
  // Set up WebSocket listeners
  useEffect(() => {
    if (!socket || !isConnected) return;
    
    const unsubscribe = on('leaderboard:update', (data: any) => {
      handleLeaderboardUpdate(data);
      setLastUpdate(new Date());
    });
    
    // Subscribe to leaderboard updates
    socket.emit('leaderboard:subscribe', {
      category: selectedCategory,
      subject: selectedSubject
    });
    
    return () => {
      socket.emit('leaderboard:unsubscribe');
      unsubscribe();
    };
  }, [socket, isConnected, selectedCategory, selectedSubject, on]);
  
  // Filter entries based on search
  useEffect(() => {
    if (!searchTerm) {
      setFilteredEntries(entries);
    } else {
      const filtered = entries.filter(entry =>
        entry.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
        entry.guildName?.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredEntries(filtered);
    }
  }, [entries, searchTerm]);
  
  const fetchLeaderboard = async () => {
    setIsLoading(true);
    try {
      // Mock data for now
      const mockData = generateMockLeaderboard();
      setEntries(mockData);
      
      // Find user's rank
      const userEntry = mockData.find(e => e.userId === user?.id);
      if (userEntry) {
        setUserRank(userEntry.rank);
      }
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleLeaderboardUpdate = (updateData: any) => {
    setEntries(prevEntries => {
      const newEntries = [...prevEntries];
      
      // Update existing entries or add new ones
      updateData.changes.forEach((change: any) => {
        const existingIndex = newEntries.findIndex(e => e.userId === change.userId);
        
        if (existingIndex >= 0) {
          // Update existing entry
          const oldRank = newEntries[existingIndex].rank;
          newEntries[existingIndex] = {
            ...newEntries[existingIndex],
            ...change,
            previousRank: oldRank,
            rankChange: change.rank < oldRank ? 'up' : change.rank > oldRank ? 'down' : 'same'
          };
        } else {
          // New entry
          newEntries.push({
            ...change,
            rankChange: 'new'
          });
          setNewEntries(prev => new Set(prev).add(change.userId));
          
          // Remove after animation
          setTimeout(() => {
            setNewEntries(prev => {
              const newSet = new Set(prev);
              newSet.delete(change.userId);
              return newSet;
            });
          }, 3000);
        }
      });
      
      // Re-sort by rank
      newEntries.sort((a, b) => a.rank - b.rank);
      
      // Limit entries
      return newEntries.slice(0, limit);
    });
    
    // Play sound for rank changes
    const userUpdate = updateData.changes.find((c: any) => c.userId === user?.id);
    if (userUpdate) {
      if (userUpdate.rankChange === 'up') {
        playSound('level_up');
      } else if (userUpdate.rankChange === 'down') {
        playSound('notification_epic');
      }
      setUserRank(userUpdate.rank);
    }
  };
  
  const generateMockLeaderboard = (): LeaderboardEntry[] => {
    const classes = ['Assassin', 'Mage', 'Warrior', 'Healer'];
    const guilds = ['Shadow Hunters', 'Math Warriors', 'Knowledge Seekers', null];
    
    return Array.from({ length: 30 }, (_, i) => ({
      rank: i + 1,
      userId: i === 5 ? (user?.id || 'user-123') : `user-${i}`,
      username: i === 5 ? (user?.name || 'Tú') : `Hunter${i + 1}`,
      level: Math.floor(Math.random() * 50) + 10,
      score: Math.floor(5000 - i * 150 + Math.random() * 100),
      accuracy: Math.floor(85 - i * 2 + Math.random() * 10),
      questionsAnswered: Math.floor(1000 - i * 30 + Math.random() * 50),
      streakDays: Math.floor(Math.random() * 30) + 1,
      guildName: guilds[Math.floor(Math.random() * guilds.length)] || undefined,
      heroClass: classes[Math.floor(Math.random() * classes.length)],
      isOnline: Math.random() > 0.5
    }));
  };
  
  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1:
        return <Crown className="w-6 h-6 text-yellow-400" />;
      case 2:
        return <Medal className="w-6 h-6 text-gray-300" />;
      case 3:
        return <Medal className="w-6 h-6 text-orange-400" />;
      default:
        return <span className="text-lg font-bold text-gray-400">#{rank}</span>;
    }
  };
  
  const getRankChangeIcon = (change?: string) => {
    switch (change) {
      case 'up':
        return <TrendingUp className="w-4 h-4 text-green-400" />;
      case 'down':
        return <TrendingDown className="w-4 h-4 text-red-400" />;
      case 'new':
        return <Sparkles className="w-4 h-4 text-purple-400" />;
      default:
        return null;
    }
  };
  
  const scrollToUser = () => {
    const userElement = document.getElementById(`leaderboard-user-${user?.id}`);
    userElement?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };
  
  return (
    <div className="bg-gray-900 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-900 to-indigo-900 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Trophy className="w-8 h-8 text-yellow-400" />
            <h2 className="text-2xl font-bold text-white font-cinzel">
              Tabla de Líderes
            </h2>
          </div>
          
          <div className="flex items-center gap-2 text-sm text-gray-300">
            <Timer className="w-4 h-4" />
            <span>Actualizado: {lastUpdate.toLocaleTimeString()}</span>
            {isConnected && (
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse ml-2" />
            )}
          </div>
        </div>
        
        {/* Filters */}
        <div className="flex flex-wrap gap-4">
          {/* Category Selector */}
          <div className="flex gap-2">
            {categories.map(cat => (
              <button
                key={cat.value}
                onClick={() => setSelectedCategory(cat.value as any)}
                className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                  selectedCategory === cat.value
                    ? 'bg-white text-purple-900'
                    : 'bg-purple-800/50 text-white hover:bg-purple-800'
                }`}
              >
                <span className="mr-2">{cat.icon}</span>
                {cat.label}
              </button>
            ))}
          </div>
          
          {/* Subject Filter */}
          <select
            value={selectedSubject}
            onChange={(e) => setSelectedSubject(e.target.value)}
            className="bg-purple-800/50 text-white px-4 py-2 rounded-lg border border-purple-700 
              focus:outline-none focus:border-purple-500"
          >
            {subjects.map(subj => (
              <option key={subj.value} value={subj.value}>
                {subj.label}
              </option>
            ))}
          </select>
          
          {/* Search */}
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar jugador o gremio..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-purple-800/50 text-white pl-10 pr-4 py-2 rounded-lg 
                  border border-purple-700 focus:outline-none focus:border-purple-500"
              />
            </div>
          </div>
        </div>
      </div>
      
      {/* User Rank Summary */}
      {userRank && (
        <div className="bg-purple-900/30 p-4 border-b border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="text-2xl font-bold text-purple-400">
                #{userRank}
              </div>
              <div>
                <p className="text-white font-semibold">Tu Posición Actual</p>
                <p className="text-sm text-gray-400">
                  {userRank <= 10 ? '¡Estás en el Top 10!' : 
                   userRank <= 50 ? 'Sigue subiendo, vas muy bien' :
                   'Continúa practicando para mejorar'}
                </p>
              </div>
            </div>
            
            <button
              onClick={scrollToUser}
              className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 
                rounded-lg transition-colors flex items-center gap-2"
            >
              <ChevronDown className="w-5 h-5" />
              Ver mi posición
            </button>
          </div>
        </div>
      )}
      
      {/* Leaderboard Table */}
      <div className="overflow-x-auto" ref={scrollRef}>
        {isLoading ? (
          <div className="flex items-center justify-center p-12">
            <motion.div
              className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full"
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            />
          </div>
        ) : filteredEntries.length === 0 ? (
          <div className="text-center p-12">
            <p className="text-gray-400">No se encontraron resultados</p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left p-4 text-gray-400 font-semibold">Rango</th>
                <th className="text-left p-4 text-gray-400 font-semibold">Jugador</th>
                <th className="text-center p-4 text-gray-400 font-semibold">Nivel</th>
                <th className="text-center p-4 text-gray-400 font-semibold">Puntuación</th>
                <th className="text-center p-4 text-gray-400 font-semibold">Precisión</th>
                <th className="text-center p-4 text-gray-400 font-semibold">Racha</th>
                <th className="text-left p-4 text-gray-400 font-semibold">Gremio</th>
              </tr>
            </thead>
            <tbody>
              <AnimatePresence mode="popLayout">
                {filteredEntries.map((entry, index) => (
                  <motion.tr
                    key={entry.userId}
                    id={`leaderboard-user-${entry.userId}`}
                    layout
                    initial={newEntries.has(entry.userId) ? { 
                      opacity: 0, 
                      x: -50,
                      backgroundColor: 'rgba(168, 85, 247, 0.2)'
                    } : { opacity: 1 }}
                    animate={{ 
                      opacity: 1, 
                      x: 0,
                      backgroundColor: entry.userId === user?.id 
                        ? 'rgba(139, 92, 246, 0.1)' 
                        : newEntries.has(entry.userId)
                        ? ['rgba(168, 85, 247, 0.2)', 'rgba(0, 0, 0, 0)']
                        : 'rgba(0, 0, 0, 0)'
                    }}
                    exit={{ opacity: 0, x: 50 }}
                    transition={{ 
                      duration: 0.3,
                      backgroundColor: { duration: 2 }
                    }}
                    className={`border-b border-gray-800 hover:bg-gray-800/50 transition-colors ${
                      entry.userId === user?.id ? 'ring-2 ring-purple-500/30' : ''
                    }`}
                  >
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        {getRankIcon(entry.rank)}
                        {getRankChangeIcon(entry.rankChange)}
                      </div>
                    </td>
                    
                    <td className="p-4">
                      <div className="flex items-center gap-3">
                        <div className="relative">
                          <div className={`w-10 h-10 rounded-full bg-gradient-to-br 
                            ${entry.rank === 1 ? 'from-yellow-400 to-yellow-600' :
                              entry.rank === 2 ? 'from-gray-300 to-gray-500' :
                              entry.rank === 3 ? 'from-orange-400 to-orange-600' :
                              'from-purple-400 to-purple-600'} 
                            flex items-center justify-center text-white font-bold`}>
                            {entry.username.charAt(0).toUpperCase()}
                          </div>
                          {entry.isOnline && (
                            <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 
                              bg-green-400 rounded-full border-2 border-gray-900" />
                          )}
                        </div>
                        
                        <div>
                          <p className="text-white font-semibold">
                            {entry.username}
                            {entry.userId === user?.id && (
                              <span className="text-purple-400 text-sm ml-2">(Tú)</span>
                            )}
                          </p>
                          <p className="text-xs text-gray-400">{entry.heroClass}</p>
                        </div>
                      </div>
                    </td>
                    
                    <td className="p-4 text-center">
                      <div className="flex items-center justify-center gap-1">
                        <Star className="w-4 h-4 text-yellow-400" />
                        <span className="text-white font-semibold">{entry.level}</span>
                      </div>
                    </td>
                    
                    <td className="p-4 text-center">
                      <motion.span
                        className="text-white font-bold"
                        key={`${entry.userId}-score`}
                        initial={{ scale: 1 }}
                        animate={entry.rankChange === 'up' ? { 
                          scale: [1, 1.2, 1] 
                        } : {}}
                        transition={{ duration: 0.3 }}
                      >
                        {entry.score.toLocaleString()}
                      </motion.span>
                    </td>
                    
                    <td className="p-4 text-center">
                      <span className={`font-semibold ${
                        entry.accuracy >= 90 ? 'text-green-400' :
                        entry.accuracy >= 80 ? 'text-blue-400' :
                        entry.accuracy >= 70 ? 'text-yellow-400' :
                        'text-red-400'
                      }`}>
                        {entry.accuracy}%
                      </span>
                    </td>
                    
                    <td className="p-4 text-center">
                      <div className="flex items-center justify-center gap-1">
                        <Zap className="w-4 h-4 text-orange-400" />
                        <span className="text-white">{entry.streakDays}</span>
                      </div>
                    </td>
                    
                    <td className="p-4">
                      {entry.guildName ? (
                        <span className="text-sm text-gray-300">{entry.guildName}</span>
                      ) : (
                        <span className="text-sm text-gray-500 italic">Sin gremio</span>
                      )}
                    </td>
                  </motion.tr>
                ))}
              </AnimatePresence>
            </tbody>
          </table>
        )}
      </div>
      
      {/* Footer */}
      <div className="bg-gray-800/50 p-4 text-center text-sm text-gray-400">
        <p>
          Las tablas se actualizan en tiempo real • 
          Los rankings se reinician {selectedCategory === 'daily' ? 'diariamente' : 
                                   selectedCategory === 'weekly' ? 'semanalmente' : 'mensualmente'}
        </p>
      </div>
    </div>
  );
}