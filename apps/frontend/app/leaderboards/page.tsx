'use client';

import React, { useState, useEffect } from 'react';
import RealtimeLeaderboard from '@/components/Leaderboards/RealtimeLeaderboard';
import { AudioProvider } from '@/components/PortalLogin/AudioEngine';
import { motion } from 'framer-motion';
import { 
  Trophy, 
  Medal, 
  Crown, 
  Star, 
  TrendingUp,
  Zap,
  Target,
  Sparkles,
  Award
} from 'lucide-react';
import { websocketService } from '../services/websocket.service';
import { cacheService } from '../services/cache.service';
import { useAnalytics } from '../services/analytics.service';
import { ErrorBoundary } from '../components/ErrorBoundary';

export default function LeaderboardsPage() {
  // Analytics hook
  const { trackPageView, trackButtonClick, trackLeaderboardView } = useAnalytics();
  const [activeTab, setActiveTab] = useState<'global' | 'weekly' | 'daily' | 'guild'>('global');
  const [leaderboardData, setLeaderboardData] = useState(null);
  const [userStats, setUserStats] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Load all data on mount for optimal performance
  useEffect(() => {
    Promise.all([
      loadUserStats(),
      loadLeaderboardData(activeTab),
      loadGuildData(),
      loadAchievements(),
      loadSeasonStats()
    ]).catch(error => {
      console.error('Error loading leaderboard data:', error);
    });
  }, []);

  // Load leaderboard data when tab changes
  useEffect(() => {
    loadLeaderboardData(activeTab);
  }, [activeTab]);

  const loadLeaderboardData = async (tab: string) => {
    try {
      setIsLoading(true);
      const endpoint = `/api/v1/leaderboard/${tab}`;
      const response = await fetch(endpoint);
      
      if (response.ok) {
        const data = await response.json();
        setLeaderboardData(data);
      }
    } catch (error) {
      console.error('Error loading leaderboard:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadUserStats = async () => {
    try {
      // Load user personal stats
      const personalResponse = await fetch('/api/v1/analytics/personal');
      if (personalResponse.ok) {
        const personalData = await personalResponse.json();
        
        // Load user ranking
        const rankingResponse = await fetch('/api/v1/leaderboard/user-ranking');
        const rankingData = rankingResponse.ok ? await rankingResponse.json() : {};
        
        setUserStats({
          ...personalData,
          ...rankingData,
          // Fallback values if API doesn't provide them
          globalRank: rankingData.globalRank || 42,
          weeklyRank: rankingData.weeklyRank || 15,
          dailyRank: rankingData.dailyRank || 8,
          totalPoints: personalData.totalPoints || 12500,
          weeklyGain: personalData.weeklyGain || 2300,
          accuracy: personalData.accuracy || 87,
          questionsAnswered: personalData.questionsAnswered || 1250,
          streakDays: personalData.streakDays || 15,
          achievements: personalData.achievements || 23
        });
      }
    } catch (error) {
      console.error('Error loading user stats:', error);
      // Fallback to mock data if API fails
      setUserStats({
        globalRank: 42,
        weeklyRank: 15,
        dailyRank: 8,
        totalPoints: 12500,
        weeklyGain: 2300,
        accuracy: 87,
        questionsAnswered: 1250,
        streakDays: 15,
        achievements: 23
      });
    }
  };

  const loadGuildData = async () => {
    try {
      const response = await fetch('/api/v1/guilds/my-guild', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const guildData = await response.json();
        console.log('Guild data loaded:', guildData.name);
      }
    } catch (error) {
      console.error('Error loading guild data:', error);
    }
  };

  const loadAchievements = async () => {
    try {
      const response = await fetch('/api/v1/achievements/user', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const achievements = await response.json();
        console.log('Achievements loaded:', achievements.length);
        // Update user stats with achievement count
        if (userStats) {
          setUserStats(prev => ({
            ...prev,
            achievements: achievements.length
          }));
        }
      }
    } catch (error) {
      console.error('Error loading achievements:', error);
    }
  };

  const loadSeasonStats = async () => {
    try {
      const response = await fetch('/api/v1/leaderboard/season-stats', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const seasonData = await response.json();
        console.log('Season stats loaded:', seasonData);
      }
    } catch (error) {
      console.error('Error loading season stats:', error);
    }
  };
  
  const tabs = [
    { 
      id: 'global' as const, 
      label: 'Global', 
      icon: '🌍',
      description: 'Ranking de todos los tiempos'
    },
    { 
      id: 'weekly' as const, 
      label: 'Semanal', 
      icon: '📅',
      description: 'Los mejores de la semana'
    },
    { 
      id: 'daily' as const, 
      label: 'Diario', 
      icon: '☀️',
      description: 'Líderes del día'
    },
    { 
      id: 'guild' as const, 
      label: 'Gremio', 
      icon: '⚔️',
      description: 'Ranking de tu gremio'
    }
  ];
  
  return (
    <AudioProvider>
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-indigo-900">
        {/* Hero Section */}
        <div className="bg-black/30 backdrop-blur-sm">
          <div className="container mx-auto px-4 py-12">
            <motion.div
              className="text-center"
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className="flex items-center justify-center gap-3 mb-4">
                <Trophy className="w-12 h-12 text-yellow-400" />
                <h1 className="text-5xl font-bold text-white font-cinzel">
                  Salón de la Fama
                </h1>
                <Trophy className="w-12 h-12 text-yellow-400" />
              </div>
              
              <p className="text-xl text-purple-300 mb-8">
                Compite con los mejores hunters y demuestra tu dominio
              </p>
              
              {/* User Quick Stats */}
              <motion.div
                className="grid grid-cols-2 md:grid-cols-5 gap-4 max-w-4xl mx-auto"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.2 }}
              >
                <div className="bg-gray-800/50 rounded-lg p-4 backdrop-blur-sm">
                  <Crown className="w-8 h-8 text-yellow-400 mx-auto mb-2" />
                  <p className="text-3xl font-bold text-white">#{userStats?.globalRank || '--'}</p>
                  <p className="text-sm text-gray-400">Rango Global</p>
                </div>
                
                <div className="bg-gray-800/50 rounded-lg p-4 backdrop-blur-sm">
                  <Star className="w-8 h-8 text-blue-400 mx-auto mb-2" />
                  <p className="text-3xl font-bold text-white">{userStats?.totalPoints?.toLocaleString() || '0'}</p>
                  <p className="text-sm text-gray-400">Puntos Totales</p>
                </div>
                
                <div className="bg-gray-800/50 rounded-lg p-4 backdrop-blur-sm">
                  <Target className="w-8 h-8 text-green-400 mx-auto mb-2" />
                  <p className="text-3xl font-bold text-white">{userStats?.accuracy || '0'}%</p>
                  <p className="text-sm text-gray-400">Precisión</p>
                </div>
                
                <div className="bg-gray-800/50 rounded-lg p-4 backdrop-blur-sm">
                  <Zap className="w-8 h-8 text-orange-400 mx-auto mb-2" />
                  <p className="text-3xl font-bold text-white">{userStats?.streakDays || '0'}</p>
                  <p className="text-sm text-gray-400">Días de Racha</p>
                </div>
                
                <div className="bg-gray-800/50 rounded-lg p-4 backdrop-blur-sm">
                  <Award className="w-8 h-8 text-purple-400 mx-auto mb-2" />
                  <p className="text-3xl font-bold text-white">{userStats?.achievements || '0'}</p>
                  <p className="text-sm text-gray-400">Logros</p>
                </div>
              </motion.div>
            </motion.div>
          </div>
        </div>
        
        {/* Main Content */}
        <div className="container mx-auto px-4 py-8">
          {/* Tab Navigation */}
          <motion.div
            className="flex flex-wrap justify-center gap-4 mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            {tabs.map((tab) => (
              <motion.button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`group relative px-6 py-4 rounded-lg font-semibold transition-all ${
                  activeTab === tab.id
                    ? 'bg-gradient-to-r from-purple-600 to-purple-700 text-white shadow-lg shadow-purple-500/30'
                    : 'bg-gray-800/50 text-gray-300 hover:bg-gray-800/70'
                }`}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{tab.icon}</span>
                  <div className="text-left">
                    <p className="font-bold">{tab.label}</p>
                    <p className="text-xs opacity-75">{tab.description}</p>
                  </div>
                </div>
                
                {activeTab === tab.id && (
                  <motion.div
                    className="absolute inset-0 rounded-lg bg-gradient-to-r from-purple-600/20 to-purple-700/20"
                    layoutId="activeTab"
                    transition={{ type: "spring", bounce: 0.3, duration: 0.6 }}
                  />
                )}
              </motion.button>
            ))}
          </motion.div>
          
          {/* Leaderboard Component */}
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            <RealtimeLeaderboard
              category={activeTab}
              subject="all"
              limit={50}
            />
          </motion.div>
          
          {/* Achievement Showcase */}
          <motion.div
            className="mt-12 bg-gray-800/30 rounded-lg p-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <h3 className="text-2xl font-bold text-white mb-6 text-center font-cinzel">
              Logros Especiales
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="w-20 h-20 mx-auto mb-3 rounded-full bg-gradient-to-br 
                  from-yellow-400 to-yellow-600 flex items-center justify-center">
                  <Crown className="w-10 h-10 text-white" />
                </div>
                <h4 className="font-semibold text-white mb-1">Rey de la Colina</h4>
                <p className="text-sm text-gray-400">Alcanza el Top 1 Global</p>
                <div className="mt-2 flex items-center justify-center gap-1">
                  <Star className="w-4 h-4 text-yellow-400" />
                  <span className="text-xs text-gray-300">0.1% jugadores</span>
                </div>
              </div>
              
              <div className="text-center">
                <div className="w-20 h-20 mx-auto mb-3 rounded-full bg-gradient-to-br 
                  from-purple-400 to-purple-600 flex items-center justify-center">
                  <Zap className="w-10 h-10 text-white" />
                </div>
                <h4 className="font-semibold text-white mb-1">Racha Legendaria</h4>
                <p className="text-sm text-gray-400">100 días consecutivos</p>
                <div className="mt-2 flex items-center justify-center gap-1">
                  <Star className="w-4 h-4 text-purple-400" />
                  <span className="text-xs text-gray-300">1% jugadores</span>
                </div>
              </div>
              
              <div className="text-center">
                <div className="w-20 h-20 mx-auto mb-3 rounded-full bg-gradient-to-br 
                  from-green-400 to-green-600 flex items-center justify-center">
                  <Target className="w-10 h-10 text-white" />
                </div>
                <h4 className="font-semibold text-white mb-1">Precisión Perfecta</h4>
                <p className="text-sm text-gray-400">100% en 1000 preguntas</p>
                <div className="mt-2 flex items-center justify-center gap-1">
                  <Star className="w-4 h-4 text-green-400" />
                  <span className="text-xs text-gray-300">0.5% jugadores</span>
                </div>
              </div>
              
              <div className="text-center">
                <div className="w-20 h-20 mx-auto mb-3 rounded-full bg-gradient-to-br 
                  from-blue-400 to-blue-600 flex items-center justify-center">
                  <TrendingUp className="w-10 h-10 text-white" />
                </div>
                <h4 className="font-semibold text-white mb-1">Ascenso Meteórico</h4>
                <p className="text-sm text-gray-400">Sube 100 rangos en un día</p>
                <div className="mt-2 flex items-center justify-center gap-1">
                  <Star className="w-4 h-4 text-blue-400" />
                  <span className="text-xs text-gray-300">5% jugadores</span>
                </div>
              </div>
            </div>
          </motion.div>
          
          {/* Tips Section */}
          <motion.div
            className="mt-8 bg-purple-900/20 rounded-lg p-6 border border-purple-500/30"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
          >
            <div className="flex items-start gap-4">
              <Sparkles className="w-8 h-8 text-purple-400 flex-shrink-0" />
              <div>
                <h4 className="font-semibold text-white mb-2">
                  Consejo del Sistema
                </h4>
                <p className="text-sm text-gray-300">
                  Para subir rápidamente en el ranking, mantén una racha diaria activa, 
                  mejora tu precisión respondiendo con cuidado, y participa en raids 
                  multijugador para obtener bonificaciones adicionales. ¡La consistencia 
                  es la clave del éxito!
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </AudioProvider>
  );
}