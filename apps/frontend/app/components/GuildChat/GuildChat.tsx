'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Send, 
  Shield, 
  Crown, 
  Users,
  MessageSquare,
  Bot,
  Sparkles,
  Ban,
  Volume2,
  VolumeX,
  Settings,
  ChevronDown
} from 'lucide-react';
import { useGuildChat } from '@/hooks/useWebSocket';
import { useAuthStore } from '@/stores/useAuthStore';
import { useAudio } from '../PortalLogin/AudioEngine';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';

interface ChatMessage {
  id: string;
  userId: string;
  username: string;
  userRole: 'member' | 'officer' | 'leader';
  userLevel: number;
  message: string;
  timestamp: Date;
  type: 'user' | 'system' | 'achievement' | 'raid';
  metadata?: {
    achievementName?: string;
    raidBossName?: string;
    damage?: number;
  };
}

interface GuildMember {
  id: string;
  username: string;
  role: 'member' | 'officer' | 'leader';
  level: number;
  isOnline: boolean;
  lastSeen?: Date;
}

interface GuildChatProps {
  guildId: string;
  guildName: string;
  maxHeight?: string;
  showMemberList?: boolean;
}

export default function GuildChat({ 
  guildId, 
  guildName, 
  maxHeight = '600px',
  showMemberList = true 
}: GuildChatProps) {
  const { user } = useAuthStore();
  const { playSound } = useAudio();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  
  const { 
    socket, 
    messages: wsMessages, 
    sendMessage: wsSendMessage,
    isConnected 
  } = useGuildChat(guildId);
  
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [typingUsers, setTypingUsers] = useState<Set<string>>(new Set());
  const [guildMembers, setGuildMembers] = useState<GuildMember[]>([]);
  const [isMuted, setIsMuted] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  
  // AI moderation suggestions
  const [aiSuggestions, setAiSuggestions] = useState<string[]>([
    '¡Felicidades por completar la mazmorra!',
    '¿Alguien quiere hacer el raid del jefe sombra?',
    'Necesito ayuda con álgebra avanzada',
    'GG equipo, gran batalla!'
  ]);
  
  // Load initial messages and members
  useEffect(() => {
    if (!socket || !isConnected) return;
    
    // Request guild info
    socket.emit('guild:join', { guildId, userId: user?.id });
    
    // Listen for messages
    socket.on('guild:message', (data: any) => {
      const newMessage: ChatMessage = {
        id: data.id || Date.now().toString(),
        userId: data.userId,
        username: data.username,
        userRole: data.userRole || 'member',
        userLevel: data.userLevel || 1,
        message: data.message,
        timestamp: new Date(data.timestamp),
        type: data.type || 'user',
        metadata: data.metadata
      };
      
      setMessages(prev => [...prev, newMessage]);
      
      if (!isMuted && data.userId !== user?.id) {
        playSound('notification_epic');
      }
    });
    
    // Listen for member updates
    socket.on('guild:members_update', (members: GuildMember[]) => {
      setGuildMembers(members);
    });
    
    // Listen for typing indicators
    socket.on('guild:typing', ({ userId, isTyping: typing }: any) => {
      setTypingUsers(prev => {
        const newSet = new Set(prev);
        if (typing && userId !== user?.id) {
          newSet.add(userId);
        } else {
          newSet.delete(userId);
        }
        return newSet;
      });
    });
    
    // Mock initial data
    setMessages([
      {
        id: '1',
        userId: 'system',
        username: 'Sistema',
        userRole: 'member',
        userLevel: 0,
        message: `Bienvenido al chat de ${guildName}`,
        timestamp: new Date(Date.now() - 3600000),
        type: 'system'
      },
      {
        id: '2',
        userId: '123',
        username: 'ShadowLeader',
        userRole: 'leader',
        userLevel: 45,
        message: '¡Hoy tenemos raid a las 8PM!',
        timestamp: new Date(Date.now() - 1800000),
        type: 'user'
      }
    ]);
    
    setGuildMembers([
      {
        id: user?.id || '1',
        username: user?.username || 'Tú',
        role: 'member',
        level: user?.level || 1,
        isOnline: true
      },
      {
        id: '123',
        username: 'ShadowLeader',
        role: 'leader',
        level: 45,
        isOnline: true
      },
      {
        id: '456',
        username: 'MathWizard',
        role: 'officer',
        level: 32,
        isOnline: true
      },
      {
        id: '789',
        username: 'DragonSlayer',
        role: 'member',
        level: 28,
        isOnline: false,
        lastSeen: new Date(Date.now() - 7200000)
      }
    ]);
    
    return () => {
      socket.emit('guild:leave', { guildId, userId: user?.id });
      socket.off('guild:message');
      socket.off('guild:members_update');
      socket.off('guild:typing');
    };
  }, [socket, isConnected, guildId, user, playSound, isMuted, guildName]);
  
  // Auto-scroll to bottom
  useEffect(() => {
    if (autoScroll) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, autoScroll]);
  
  // Handle typing indicator
  useEffect(() => {
    if (!socket || !isTyping) return;
    
    const timeout = setTimeout(() => {
      socket.emit('guild:typing', { 
        guildId, 
        userId: user?.id, 
        isTyping: false 
      });
      setIsTyping(false);
    }, 2000);
    
    return () => clearTimeout(timeout);
  }, [isTyping, socket, guildId, user]);
  
  const handleSendMessage = () => {
    if (!inputMessage.trim() || !socket || !isConnected) return;
    
    const messageData = {
      guildId,
      userId: user?.id,
      username: user?.username || 'Anonymous',
      userRole: 'member' as const,
      userLevel: user?.level || 1,
      message: inputMessage.trim(),
      timestamp: new Date(),
      type: 'user' as const
    };
    
    socket.emit('guild:message', messageData);
    
    // Add message locally for instant feedback
    setMessages(prev => [...prev, {
      ...messageData,
      id: Date.now().toString()
    }]);
    
    setInputMessage('');
    setIsTyping(false);
    playSound('typing_click');
  };
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputMessage(e.target.value);
    
    if (!isTyping && e.target.value.length > 0 && socket) {
      setIsTyping(true);
      socket.emit('guild:typing', { 
        guildId, 
        userId: user?.id, 
        isTyping: true 
      });
    }
  };
  
  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'leader':
        return <Crown className="w-4 h-4 text-yellow-400" />;
      case 'officer':
        return <Shield className="w-4 h-4 text-blue-400" />;
      default:
        return null;
    }
  };
  
  const getMessageColor = (type: string) => {
    switch (type) {
      case 'system':
        return 'text-gray-400';
      case 'achievement':
        return 'text-green-400';
      case 'raid':
        return 'text-purple-400';
      default:
        return 'text-white';
    }
  };
  
  return (
    <div className="bg-gray-900 rounded-lg overflow-hidden flex" style={{ maxHeight }}>
      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-gray-800 p-4 border-b border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <MessageSquare className="w-6 h-6 text-purple-400" />
              <h3 className="text-lg font-semibold text-white">{guildName}</h3>
              <span className="text-sm text-gray-400">
                {guildMembers.filter(m => m.isOnline).length} en línea
              </span>
            </div>
            
            <div className="flex items-center gap-2">
              <button
                onClick={() => setAutoScroll(!autoScroll)}
                className={`p-2 rounded hover:bg-gray-700 transition-colors ${
                  autoScroll ? 'text-purple-400' : 'text-gray-400'
                }`}
                title={autoScroll ? 'Auto-scroll activado' : 'Auto-scroll desactivado'}
              >
                <ChevronDown className="w-5 h-5" />
              </button>
              
              <button
                onClick={() => setIsMuted(!isMuted)}
                className={`p-2 rounded hover:bg-gray-700 transition-colors ${
                  isMuted ? 'text-red-400' : 'text-gray-400'
                }`}
              >
                {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
              </button>
              
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="p-2 rounded hover:bg-gray-700 transition-colors text-gray-400"
              >
                <Settings className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
        
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message, index) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className={`${message.userId === user?.id ? 'text-right' : ''}`}
            >
              <div className={`inline-block max-w-[70%] ${
                message.userId === user?.id ? 'ml-auto' : ''
              }`}>
                {/* User info */}
                {message.type === 'user' && (
                  <div className={`flex items-center gap-2 mb-1 ${
                    message.userId === user?.id ? 'justify-end' : ''
                  }`}>
                    <span className="text-sm font-semibold text-gray-300">
                      {message.username}
                    </span>
                    {getRoleIcon(message.userRole)}
                    <span className="text-xs text-gray-500">
                      Nv.{message.userLevel}
                    </span>
                  </div>
                )}
                
                {/* Message bubble */}
                <div className={`rounded-lg px-4 py-2 ${
                  message.type === 'system' 
                    ? 'bg-gray-800 text-center' 
                    : message.userId === user?.id
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-800 text-white'
                }`}>
                  {message.type === 'achievement' && (
                    <div className="flex items-center gap-2 mb-1">
                      <Sparkles className="w-4 h-4 text-yellow-400" />
                      <span className="text-sm text-yellow-400">¡Logro Desbloqueado!</span>
                    </div>
                  )}
                  
                  <p className={getMessageColor(message.type)}>
                    {message.message}
                  </p>
                  
                  {message.metadata?.achievementName && (
                    <p className="text-sm text-yellow-300 mt-1">
                      "{message.metadata.achievementName}"
                    </p>
                  )}
                </div>
                
                {/* Timestamp */}
                <p className={`text-xs text-gray-500 mt-1 ${
                  message.userId === user?.id ? 'text-right' : ''
                }`}>
                  {formatDistanceToNow(message.timestamp, { 
                    addSuffix: true,
                    locale: es 
                  })}
                </p>
              </div>
            </motion.div>
          ))}
          
          {/* Typing indicators */}
          {typingUsers.size > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center gap-2 text-gray-400 text-sm"
            >
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
              </div>
              <span>
                {Array.from(typingUsers).length} escribiendo...
              </span>
            </motion.div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
        
        {/* AI Suggestions */}
        <div className="px-4 py-2 border-t border-gray-800">
          <div className="flex gap-2 overflow-x-auto scrollbar-hide">
            {aiSuggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => {
                  setInputMessage(suggestion);
                  inputRef.current?.focus();
                }}
                className="flex items-center gap-1 bg-gray-800 hover:bg-gray-700 
                  text-gray-300 text-xs px-3 py-1.5 rounded-full whitespace-nowrap 
                  transition-colors"
              >
                <Bot className="w-3 h-3 text-purple-400" />
                {suggestion}
              </button>
            ))}
          </div>
        </div>
        
        {/* Input */}
        <form 
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="p-4 bg-gray-800 border-t border-gray-700"
        >
          <div className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={inputMessage}
              onChange={handleInputChange}
              placeholder={isConnected ? "Escribe un mensaje..." : "Conectando..."}
              disabled={!isConnected}
              className="flex-1 bg-gray-700 text-white px-4 py-2 rounded-lg 
                focus:outline-none focus:ring-2 focus:ring-purple-500 
                disabled:opacity-50 disabled:cursor-not-allowed"
              maxLength={500}
            />
            <motion.button
              type="submit"
              disabled={!inputMessage.trim() || !isConnected}
              className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 
                disabled:cursor-not-allowed text-white p-2 rounded-lg 
                transition-colors"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Send className="w-5 h-5" />
            </motion.button>
          </div>
          <div className="flex justify-between mt-2">
            <span className="text-xs text-gray-500">
              {inputMessage.length}/500
            </span>
            {!isConnected && (
              <span className="text-xs text-red-400">
                Desconectado - Reconectando...
              </span>
            )}
          </div>
        </form>
      </div>
      
      {/* Members List */}
      {showMemberList && (
        <div className="w-64 bg-gray-800 border-l border-gray-700 p-4">
          <h4 className="text-sm font-semibold text-gray-400 mb-3">
            MIEMBROS ({guildMembers.length})
          </h4>
          
          <div className="space-y-1">
            {/* Online members */}
            {guildMembers
              .filter(m => m.isOnline)
              .sort((a, b) => {
                const roleOrder = { leader: 0, officer: 1, member: 2 };
                return roleOrder[a.role] - roleOrder[b.role];
              })
              .map(member => (
                <div
                  key={member.id}
                  className="flex items-center gap-2 p-2 rounded hover:bg-gray-700 
                    transition-colors cursor-pointer"
                >
                  <div className="w-2 h-2 bg-green-400 rounded-full" />
                  {getRoleIcon(member.role)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white truncate">
                      {member.username}
                      {member.id === user?.id && ' (Tú)'}
                    </p>
                    <p className="text-xs text-gray-500">Nv.{member.level}</p>
                  </div>
                </div>
              ))}
            
            {/* Offline members */}
            <div className="mt-4 pt-4 border-t border-gray-700">
              <p className="text-xs text-gray-500 mb-2">DESCONECTADO</p>
              {guildMembers
                .filter(m => !m.isOnline)
                .map(member => (
                  <div
                    key={member.id}
                    className="flex items-center gap-2 p-2 rounded hover:bg-gray-700 
                      transition-colors cursor-pointer opacity-50"
                  >
                    <div className="w-2 h-2 bg-gray-500 rounded-full" />
                    {getRoleIcon(member.role)}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-400 truncate">
                        {member.username}
                      </p>
                      <p className="text-xs text-gray-600">
                        {member.lastSeen && formatDistanceToNow(member.lastSeen, { 
                          addSuffix: true,
                          locale: es 
                        })}
                      </p>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}