'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChatBubbleLeftRightIcon, 
  LightBulbIcon, 
  AcademicCapIcon,
  SparklesIcon,
  ArrowPathIcon,
  PlayIcon,
  StopIcon
} from '@heroicons/react/24/outline';

interface AIMessage {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
  metadata?: {
    confidence_score?: number;
    interaction_type?: string;
    follow_up_questions?: string[];
    suggested_actions?: string[];
    estimated_time?: number;
  };
}

interface AITutorProps {
  studentId: string;
  subjectId?: number;
  initialContext?: string;
  onInteraction?: (interaction: any) => void;
}

export default function AITutor({ 
  studentId, 
  subjectId, 
  initialContext = "general",
  onInteraction 
}: AITutorProps) {
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [contextType, setContextType] = useState(initialContext);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  // Quick suggestion prompts for different contexts
  const quickSuggestions = {
    general: [
      "¿Cómo puedo mejorar mi rendimiento en matemáticas?",
      "Explícame los conceptos básicos de álgebra",
      "¿Qué estrategias me recomiendas para el ICFES?",
      "Tengo dificultades con comprensión de lectura"
    ],
    homework: [
      "¿Puedes ayudarme con esta ecuación?",
      "No entiendo este concepto de física",
      "¿Cómo resuelvo problemas de geometría?",
      "Necesito ayuda con análisis de textos"
    ],
    exam_prep: [
      "¿Cómo me preparo para el examen ICFES?",
      "¿Qué temas debo repasar más?",
      "Estrategias para manejar el tiempo en exámenes",
      "¿Cómo controlar los nervios durante el examen?"
    ],
    concept_review: [
      "Explícame las funciones matemáticas",
      "¿Qué es el análisis sintáctico?",
      "Conceptos básicos de química orgánica",
      "Historia de Colombia en el siglo XX"
    ]
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Initialize with welcome message
    if (messages.length === 0) {
      addAIMessage(
        "¡Hola! Soy tu tutor de IA especializado en ICFES. Estoy aquí para ayudarte con cualquier duda que tengas. ¿En qué puedo asistirte hoy?",
        { confidence_score: 1.0, interaction_type: 'welcome' }
      );
    }
  }, []);

  // Initialize speech recognition
  useEffect(() => {
    if (typeof window !== 'undefined' && 'webkitSpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'es-ES';

      recognitionRef.current.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInputMessage(transcript);
        setIsListening(false);
      };

      recognitionRef.current.onerror = () => {
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const addUserMessage = (content: string) => {
    const newMessage: AIMessage = {
      id: Date.now().toString(),
      type: 'user',
      content,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, newMessage]);
    return newMessage;
  };

  const addAIMessage = (content: string, metadata?: any) => {
    const newMessage: AIMessage = {
      id: Date.now().toString() + '_ai',
      type: 'ai',
      content,
      timestamp: new Date(),
      metadata
    };
    setMessages(prev => [...prev, newMessage]);
    return newMessage;
  };

  const sendMessage = async (messageContent?: string) => {
    const content = messageContent || inputMessage.trim();
    if (!content || isLoading) return;

    setInputMessage('');
    setShowSuggestions(false);
    setIsLoading(true);

    // Add user message
    addUserMessage(content);

    try {
      const response = await fetch('/api/ai-training/tutor-chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          message: content,
          context_type: contextType,
          subject_id: subjectId
        })
      });

      if (!response.ok) {
        throw new Error('Failed to get AI response');
      }

      const aiResponse = await response.json();

      // Add AI response
      addAIMessage(aiResponse.response_text, {
        confidence_score: aiResponse.confidence_score,
        interaction_type: aiResponse.interaction_type,
        follow_up_questions: aiResponse.follow_up_questions,
        suggested_actions: aiResponse.suggested_actions,
        estimated_time: aiResponse.estimated_time_needed
      });

      // Notify parent component
      if (onInteraction) {
        onInteraction({
          type: 'chat',
          response: aiResponse,
          user_message: content
        });
      }

    } catch (error) {
      console.error('AI Chat Error:', error);
      addAIMessage(
        "Disculpa, hubo un problema procesando tu mensaje. ¿Podrías intentar de nuevo o reformular tu pregunta?",
        { confidence_score: 0.5, interaction_type: 'error' }
      );
    } finally {
      setIsLoading(false);
    }
  };

  const startVoiceInput = () => {
    if (recognitionRef.current && !isListening) {
      setIsListening(true);
      recognitionRef.current.start();
    }
  };

  const stopVoiceInput = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    sendMessage(suggestion);
  };

  const handleFollowUpClick = (question: string) => {
    sendMessage(question);
  };

  const formatAIMessage = (message: AIMessage) => {
    const { content, metadata } = message;
    
    return (
      <div className="space-y-4">
        {/* Main response */}
        <div className="prose prose-sm max-w-none text-gray-700 dark:text-gray-300">
          {content.split('\n').map((paragraph, index) => (
            <p key={index} className="mb-2">{paragraph}</p>
          ))}
        </div>

        {/* Confidence indicator */}
        {metadata?.confidence_score && (
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            <SparklesIcon className="h-3 w-3" />
            <span>Confianza: {(metadata.confidence_score * 100).toFixed(0)}%</span>
          </div>
        )}

        {/* Follow-up questions */}
        {metadata?.follow_up_questions && metadata.follow_up_questions.length > 0 && (
          <div className="mt-3">
            <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">
              Preguntas sugeridas:
            </p>
            <div className="space-y-1">
              {metadata.follow_up_questions.map((question: string, index: number) => (
                <button
                  key={index}
                  onClick={() => handleFollowUpClick(question)}
                  className="block w-full text-left text-xs bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 px-3 py-2 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Suggested actions */}
        {metadata?.suggested_actions && metadata.suggested_actions.length > 0 && (
          <div className="mt-3">
            <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">
              Acciones recomendadas:
            </p>
            <div className="space-y-1">
              {metadata.suggested_actions.slice(0, 3).map((action: string, index: number) => (
                <div key={index} className="flex items-start space-x-2 text-xs text-gray-600 dark:text-gray-400">
                  <div className="w-1 h-1 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
                  <span>{action}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Estimated time */}
        {metadata?.estimated_time && (
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            <AcademicCapIcon className="h-3 w-3" />
            <span>Tiempo estimado: {metadata.estimated_time} minutos</span>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900 rounded-xl shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg">
            <ChatBubbleLeftRightIcon className="h-5 w-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white">
              Tutor IA
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Especialista en ICFES
            </p>
          </div>
        </div>

        {/* Context selector */}
        <select
          value={contextType}
          onChange={(e) => setContextType(e.target.value)}
          className="text-xs bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg px-2 py-1"
        >
          <option value="general">General</option>
          <option value="homework">Tareas</option>
          <option value="exam_prep">Preparación</option>
          <option value="concept_review">Conceptos</option>
        </select>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-xl px-4 py-3 ${
                  message.type === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white'
                }`}
              >
                {message.type === 'user' ? (
                  <p className="text-sm">{message.content}</p>
                ) : (
                  formatAIMessage(message)
                )}
                
                <p className="text-xs opacity-70 mt-2">
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Loading indicator */}
        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-start"
          >
            <div className="bg-gray-100 dark:bg-gray-800 rounded-xl px-4 py-3">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Quick suggestions */}
        {showSuggestions && messages.length <= 1 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-2"
          >
            <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Sugerencias para empezar:
            </p>
            <div className="grid grid-cols-1 gap-2">
              {quickSuggestions[contextType as keyof typeof quickSuggestions]?.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="text-left text-sm bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors border border-gray-200 dark:border-gray-600"
                >
                  <LightBulbIcon className="h-4 w-4 inline mr-2 text-yellow-500" />
                  {suggestion}
                </button>
              ))}
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex space-x-2">
          <div className="flex-1 relative">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Escribe tu pregunta aquí..."
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              disabled={isLoading}
            />
            
            {/* Voice input button */}
            {recognitionRef.current && (
              <button
                onClick={isListening ? stopVoiceInput : startVoiceInput}
                className={`absolute right-2 top-1/2 transform -translate-y-1/2 p-1 rounded-full ${
                  isListening 
                    ? 'bg-red-500 text-white' 
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-300 dark:hover:bg-gray-600'
                }`}
                title={isListening ? "Detener grabación" : "Grabar mensaje"}
              >
                {isListening ? (
                  <StopIcon className="h-4 w-4" />
                ) : (
                  <PlayIcon className="h-4 w-4" />
                )}
              </button>
            )}
          </div>
          
          <button
            onClick={() => sendMessage()}
            disabled={!inputMessage.trim() || isLoading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
          >
            {isLoading ? (
              <ArrowPathIcon className="h-4 w-4 animate-spin" />
            ) : (
              <ChatBubbleLeftRightIcon className="h-4 w-4" />
            )}
            <span>Enviar</span>
          </button>
        </div>
        
        {isListening && (
          <p className="text-xs text-red-600 dark:text-red-400 mt-2 animate-pulse">
            🎤 Escuchando... Habla ahora
          </p>
        )}
      </div>
    </div>
  );
}