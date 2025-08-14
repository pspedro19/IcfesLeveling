'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Sparkles, 
  MessageSquare, 
  BookOpen, 
  Lightbulb, 
  Heart, 
  X,
  Send,
  Bot
} from 'lucide-react';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
}

interface AITutorAssistantProps {
  context?: string;
  isExpanded: boolean;
  onToggle: () => void;
  className?: string;
}

function MessageBubble({ message, isAI }: { message: Message; isAI: boolean }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isAI ? 'justify-start' : 'justify-end'} mb-3`}
    >
      <div className={`max-w-xs px-3 py-2 rounded-lg ${
        isAI 
          ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-200' 
          : 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200'
      }`}>
        <p className="text-sm">{message.text}</p>
        <span className="text-xs opacity-60 mt-1 block">
          {message.timestamp.toLocaleTimeString()}
        </span>
      </div>
    </motion.div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex justify-start mb-3">
      <div className="bg-purple-100 dark:bg-purple-900/30 px-3 py-2 rounded-lg">
        <div className="flex space-x-1">
          <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" />
          <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
          <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
        </div>
      </div>
    </div>
  );
}

function QuickAction({ label, icon, onClick }: { 
  label: string; 
  icon: React.ReactNode; 
  onClick: () => void;
}) {
  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      className="flex-1 p-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg 
                 hover:bg-purple-100 dark:hover:bg-purple-900/40 transition-colors"
    >
      <div className="text-center">
        <div className="flex justify-center mb-1 text-purple-600 dark:text-purple-400">
          {icon}
        </div>
        <span className="text-xs text-purple-700 dark:text-purple-300 font-medium">
          {label}
        </span>
      </div>
    </motion.button>
  );
}

export function AITutorAssistant({ 
  context, 
  isExpanded, 
  onToggle, 
  className = '' 
}: AITutorAssistantProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: '¡Hola! Soy tu tutor de IA. ¿En qué puedo ayudarte hoy?',
      sender: 'ai',
      timestamp: new Date()
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const handleSendMessage = () => {
    if (!inputText.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Entiendo tu pregunta. Te ayudo a resolverla paso a paso...',
        sender: 'ai',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, aiMessage]);
      setIsTyping(false);
    }, 2000);
  };

  const handleQuickAction = (action: string) => {
    const actionMessages = {
      'explain': '¿Qué concepto te gustaría que te explique?',
      'hint': 'Te daré una pista útil para resolver tu problema...',
      'motivation': '¡Tú puedes! Recuerda que cada error es una oportunidad de aprender.'
    };

    const aiMessage: Message = {
      id: Date.now().toString(),
      text: actionMessages[action as keyof typeof actionMessages] || 'Te ayudo con eso...',
      sender: 'ai',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, aiMessage]);
  };

  return (
    <motion.div
      initial={{ width: isExpanded ? 320 : 60 }}
      animate={{ width: isExpanded ? 320 : 60 }}
      className={`fixed right-4 bottom-4 bg-white dark:bg-gray-800 
                 rounded-2xl shadow-xl border-2 border-purple-500 z-50 ${className}`}
    >
      {isExpanded ? (
        <div className="flex flex-col h-96">
          {/* Header */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 
                                rounded-full flex items-center justify-center">
                  <Bot className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900 dark:text-white">
                    Oráculo IA
                  </h3>
                  <span className="text-xs text-purple-600 dark:text-purple-400">
                    Tu tutor personal
                  </span>
                </div>
              </div>
              <button
                onClick={onToggle}
                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <X className="w-4 h-4 text-gray-500" />
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} isAI={msg.sender === 'ai'} />
            ))}
            {isTyping && <TypingIndicator />}
          </div>

          {/* Quick Actions */}
          <div className="p-3 border-t border-gray-200 dark:border-gray-700">
            <div className="flex gap-2 mb-3">
              <QuickAction 
                label="Explicar concepto" 
                icon={<BookOpen className="w-4 h-4" />} 
                onClick={() => handleQuickAction('explain')}
              />
              <QuickAction 
                label="Dar pista" 
                icon={<Lightbulb className="w-4 h-4" />} 
                onClick={() => handleQuickAction('hint')}
              />
              <QuickAction 
                label="Motivación" 
                icon={<Heart className="w-4 h-4" />} 
                onClick={() => handleQuickAction('motivation')}
              />
            </div>

            {/* Input */}
            <div className="flex gap-2">
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Escribe tu pregunta..."
                className="flex-1 px-3 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg 
                           text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
              <button
                onClick={handleSendMessage}
                className="p-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg 
                           transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      ) : (
        <button 
          onClick={onToggle}
          className="p-4 hover:bg-purple-50 dark:hover:bg-purple-900/20 
                     transition-colors rounded-2xl"
          title="Abrir tutor de IA"
        >
          <Sparkles className="w-6 h-6 text-purple-500" />
        </button>
      )}
    </motion.div>
  );
}
