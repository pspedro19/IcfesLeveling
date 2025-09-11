'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import { useAuthStore } from '@/stores/useAuthStore';

interface RealtimeEvent {
  type: 'PROGRESS_UPDATE' | 'XP_GAINED' | 'LEVEL_UP' | 'ACHIEVEMENT_UNLOCKED' | 'RANKING_CHANGED' | 'NEW_RECOMMENDATION';
  data: any;
  timestamp: string;
}

interface ProgressUpdate {
  taskId: string;
  progress: number;
  completed: boolean;
  xpGained?: number;
}

interface XPUpdate {
  amount: number;
  source: string;
  newTotal: number;
}

interface LevelUpEvent {
  newLevel: number;
  newRank: string;
  bonusXP: number;
}

interface AchievementEvent {
  id: string;
  name: string;
  description: string;
  icon: string;
  xpReward: number;
  rarity: string;
}

interface RankingUpdate {
  classRanking: number;
  nationalRanking: number;
  change: number;
}

interface NewRecommendation {
  id: string;
  type: string;
  title: string;
  priority: string;
  estimatedTime: number;
}

export interface RealtimeState {
  isConnected: boolean;
  events: RealtimeEvent[];
  progressUpdates: ProgressUpdate[];
  xpUpdates: XPUpdate[];
  levelUps: LevelUpEvent[];
  achievements: AchievementEvent[];
  rankingUpdates: RankingUpdate[];
  recommendations: NewRecommendation[];
}

export const useRealtimeUpdates = () => {
  const { user } = useAuthStore();
  const [socket, setSocket] = useState<Socket | null>(null);
  const [state, setState] = useState<RealtimeState>({
    isConnected: false,
    events: [],
    progressUpdates: [],
    xpUpdates: [],
    levelUps: [],
    achievements: [],
    rankingUpdates: [],
    recommendations: []
  });
  
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const maxReconnectAttempts = 5;
  const reconnectAttempts = useRef(0);

  const connectSocket = useCallback(() => {
    if (!user?.id) return;

    const socketUrl = process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'http://localhost:3001';
    
    const newSocket = io(socketUrl, {
      auth: {
        userId: user.id,
        token: localStorage.getItem('auth_token')
      },
      transports: ['websocket', 'polling'],
      timeout: 20000,
      forceNew: true
    });

    // Connection events
    newSocket.on('connect', () => {
      console.log('WebSocket connected');
      setState(prev => ({ ...prev, isConnected: true }));
      reconnectAttempts.current = 0;
      
      // Join user-specific room
      newSocket.emit('join_user_room', { userId: user.id });
    });

    newSocket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      setState(prev => ({ ...prev, isConnected: false }));
      
      // Auto-reconnect logic
      if (reason === 'io server disconnect') {
        // Server initiated disconnect, don't reconnect
        return;
      }
      
      if (reconnectAttempts.current < maxReconnectAttempts) {
        reconnectAttempts.current++;
        const delay = Math.pow(2, reconnectAttempts.current) * 1000; // Exponential backoff
        
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log(`Attempting to reconnect (${reconnectAttempts.current}/${maxReconnectAttempts})`);
          newSocket.connect();
        }, delay);
      }
    });

    newSocket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      setState(prev => ({ ...prev, isConnected: false }));
    });

    // Real-time event handlers
    newSocket.on('progress_update', (data: ProgressUpdate) => {
      setState(prev => ({
        ...prev,
        progressUpdates: [data, ...prev.progressUpdates].slice(0, 50),
        events: [{
          type: 'PROGRESS_UPDATE',
          data,
          timestamp: new Date().toISOString()
        }, ...prev.events].slice(0, 100)
      }));
    });

    newSocket.on('xp_gained', (data: XPUpdate) => {
      setState(prev => ({
        ...prev,
        xpUpdates: [data, ...prev.xpUpdates].slice(0, 20),
        events: [{
          type: 'XP_GAINED',
          data,
          timestamp: new Date().toISOString()
        }, ...prev.events].slice(0, 100)
      }));
    });

    newSocket.on('level_up', (data: LevelUpEvent) => {
      setState(prev => ({
        ...prev,
        levelUps: [data, ...prev.levelUps].slice(0, 10),
        events: [{
          type: 'LEVEL_UP',
          data,
          timestamp: new Date().toISOString()
        }, ...prev.events].slice(0, 100)
      }));
    });

    newSocket.on('achievement_unlocked', (data: AchievementEvent) => {
      setState(prev => ({
        ...prev,
        achievements: [data, ...prev.achievements].slice(0, 20),
        events: [{
          type: 'ACHIEVEMENT_UNLOCKED',
          data,
          timestamp: new Date().toISOString()
        }, ...prev.events].slice(0, 100)
      }));
    });

    newSocket.on('ranking_changed', (data: RankingUpdate) => {
      setState(prev => ({
        ...prev,
        rankingUpdates: [data, ...prev.rankingUpdates].slice(0, 10),
        events: [{
          type: 'RANKING_CHANGED',
          data,
          timestamp: new Date().toISOString()
        }, ...prev.events].slice(0, 100)
      }));
    });

    newSocket.on('new_recommendation', (data: NewRecommendation) => {
      setState(prev => ({
        ...prev,
        recommendations: [data, ...prev.recommendations].slice(0, 10),
        events: [{
          type: 'NEW_RECOMMENDATION',
          data,
          timestamp: new Date().toISOString()
        }, ...prev.events].slice(0, 100)
      }));
    });

    setSocket(newSocket);

    return newSocket;
  }, [user?.id]);

  const disconnectSocket = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (socket) {
      socket.disconnect();
      setSocket(null);
    }
    
    setState(prev => ({ ...prev, isConnected: false }));
  }, [socket]);

  // Initialize connection
  useEffect(() => {
    if (user?.id) {
      const newSocket = connectSocket();
      
      return () => {
        if (newSocket) {
          newSocket.disconnect();
        }
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }
      };
    }
  }, [user?.id, connectSocket]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnectSocket();
    };
  }, [disconnectSocket]);

  // Methods to emit events
  const updateTaskProgress = useCallback((taskId: string, progress: number) => {
    if (socket?.connected) {
      socket.emit('update_task_progress', { taskId, progress });
    }
  }, [socket]);

  const markErrorAsReviewed = useCallback((errorId: string) => {
    if (socket?.connected) {
      socket.emit('mark_error_reviewed', { errorId });
    }
  }, [socket]);

  const requestNewRecommendations = useCallback(() => {
    if (socket?.connected) {
      socket.emit('request_new_recommendations');
    }
  }, [socket]);

  const trackStudySession = useCallback((sessionData: {
    subject: string;
    duration: number;
    questionsAnswered: number;
    accuracy: number;
  }) => {
    if (socket?.connected) {
      socket.emit('track_study_session', sessionData);
    }
  }, [socket]);

  // Clear specific event types
  const clearProgressUpdates = useCallback(() => {
    setState(prev => ({ ...prev, progressUpdates: [] }));
  }, []);

  const clearXPUpdates = useCallback(() => {
    setState(prev => ({ ...prev, xpUpdates: [] }));
  }, []);

  const clearEvents = useCallback(() => {
    setState(prev => ({ ...prev, events: [] }));
  }, []);

  // Get latest events by type
  const getLatestProgressUpdate = useCallback(() => {
    return state.progressUpdates[0] || null;
  }, [state.progressUpdates]);

  const getLatestXPUpdate = useCallback(() => {
    return state.xpUpdates[0] || null;
  }, [state.xpUpdates]);

  const getLatestLevelUp = useCallback(() => {
    return state.levelUps[0] || null;
  }, [state.levelUps]);

  const getLatestAchievement = useCallback(() => {
    return state.achievements[0] || null;
  }, [state.achievements]);

  const getUnreadEvents = useCallback(() => {
    return state.events.filter(event => {
      const eventTime = new Date(event.timestamp);
      const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
      return eventTime > oneHourAgo;
    });
  }, [state.events]);

  return {
    // Connection state
    isConnected: state.isConnected,
    socket,
    
    // Event data
    events: state.events,
    progressUpdates: state.progressUpdates,
    xpUpdates: state.xpUpdates,
    levelUps: state.levelUps,
    achievements: state.achievements,
    rankingUpdates: state.rankingUpdates,
    recommendations: state.recommendations,
    
    // Methods
    connectSocket,
    disconnectSocket,
    updateTaskProgress,
    markErrorAsReviewed,
    requestNewRecommendations,
    trackStudySession,
    
    // Cleanup methods
    clearProgressUpdates,
    clearXPUpdates,
    clearEvents,
    
    // Getter methods
    getLatestProgressUpdate,
    getLatestXPUpdate,
    getLatestLevelUp,
    getLatestAchievement,
    getUnreadEvents
  };
};