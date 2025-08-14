import { useEffect, useRef, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';

interface UseWebSocketProps {
  url?: string;
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

interface WebSocketState {
  isConnected: boolean;
  lastPing?: number;
  error?: string;
}

export function useWebSocket({
      url = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:4002',
  autoConnect = true,
  reconnectAttempts = 5,
  reconnectDelay = 1000
}: UseWebSocketProps = {}) {
  const socketRef = useRef<Socket | null>(null);
  const [state, setState] = useState<WebSocketState>({
    isConnected: false
  });
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectCountRef = useRef(0);

  // Initialize socket connection
  const connect = useCallback(() => {
    if (socketRef.current?.connected) return;

    socketRef.current = io(url, {
      transports: ['websocket'],
      reconnection: false // We'll handle reconnection manually
    });

    // Connection events
    socketRef.current.on('connect', () => {
      console.log('WebSocket connected');
      setState(prev => ({ ...prev, isConnected: true, error: undefined }));
      reconnectCountRef.current = 0;
    });

    socketRef.current.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      setState(prev => ({ ...prev, isConnected: false }));
      
      // Attempt reconnection
      if (reconnectCountRef.current < reconnectAttempts) {
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectCountRef.current++;
          connect();
        }, reconnectDelay * Math.pow(2, reconnectCountRef.current));
      }
    });

    socketRef.current.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      setState(prev => ({ ...prev, error: error.message }));
    });

    // Ping/pong for connection health
    socketRef.current.on('pong', (latency: number) => {
      setState(prev => ({ ...prev, lastPing: latency }));
    });
  }, [url, reconnectAttempts, reconnectDelay]);

  // Disconnect socket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    socketRef.current?.disconnect();
    setState({ isConnected: false });
  }, []);

  // Send event
  const emit = useCallback((event: string, data?: any) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit(event, data);
    } else {
      console.warn('Socket not connected. Cannot emit event:', event);
    }
  }, []);

  // Subscribe to event
  const on = useCallback((event: string, handler: (...args: any[]) => void) => {
    socketRef.current?.on(event, handler);
    
    // Return cleanup function
    return () => {
      socketRef.current?.off(event, handler);
    };
  }, []);

  // Subscribe to event (once)
  const once = useCallback((event: string, handler: (...args: any[]) => void) => {
    socketRef.current?.once(event, handler);
  }, []);

  // Initialize connection
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    socket: socketRef.current,
    isConnected: state.isConnected,
    lastPing: state.lastPing,
    error: state.error,
    connect,
    disconnect,
    emit,
    on,
    once
  };
}

// Specialized hook for raid functionality
export function useRaidSocket() {
  const { socket, isConnected, emit, on } = useWebSocket();
  const [raidState, setRaidState] = useState<any>(null);
  const [participants, setParticipants] = useState<any[]>([]);

  useEffect(() => {
    if (!isConnected) return;

    const unsubscribe = [
      on('raid:state_update', (state) => {
        setRaidState(state);
      }),
      on('raid:participant_update', (participants) => {
        setParticipants(participants);
      }),
      on('raid:damage_dealt', (data) => {
        // Handle damage animation
        console.log('Damage dealt:', data);
      }),
      on('raid:loot_distributed', (loot) => {
        // Handle loot distribution
        console.log('Loot received:', loot);
      })
    ];

    return () => {
      unsubscribe.forEach(unsub => unsub());
    };
  }, [isConnected, on]);

  const joinRaid = (raidId: string, userId: string) => {
    emit('raid:join', { raidId, userId });
  };

  const attackBoss = (raidId: string, damage: number) => {
    emit('raid:attack', { raidId, damage });
  };

  const sendMessage = (raidId: string, message: string) => {
    emit('raid:message', { raidId, message });
  };

  return {
    isConnected,
    raidState,
    participants,
    joinRaid,
    attackBoss,
    sendMessage
  };
}

// Guild chat functionality
export function useGuildChat(guildId: string) {
  const { socket, isConnected, emit, on } = useWebSocket();
  const [messages, setMessages] = useState<any[]>([]);
  const [onlineMembers, setOnlineMembers] = useState<string[]>([]);

  useEffect(() => {
    if (!isConnected || !guildId) return;

    // Join guild room
    emit('guild:join', { guildId });

    const unsubscribe = [
      on('guild:message', (message) => {
        setMessages(prev => [...prev, message]);
      }),
      on('guild:members_online', (members) => {
        setOnlineMembers(members);
      }),
      on('guild:member_joined', (member) => {
        setOnlineMembers(prev => [...prev, member]);
      }),
      on('guild:member_left', (memberId) => {
        setOnlineMembers(prev => prev.filter(id => id !== memberId));
      })
    ];

    return () => {
      emit('guild:leave', { guildId });
      unsubscribe.forEach(unsub => unsub());
    };
  }, [isConnected, guildId, emit, on]);

  const sendMessage = (message: string) => {
    emit('guild:send_message', { guildId, message });
  };

  const sendEmoji = (emoji: string, targetUserId?: string) => {
    emit('guild:send_emoji', { guildId, emoji, targetUserId });
  };

  return {
    socket,
    isConnected,
    messages,
    onlineMembers,
    sendMessage,
    sendEmoji
  };
}