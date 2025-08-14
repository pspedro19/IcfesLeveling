'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Brain, 
  MessageSquare, 
  Send,
  Sparkles,
  BookOpen,
  Target,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  X,
  Mic,
  Volume2,
  Loader2
} from 'lucide-react';
import { useAudio } from '../PortalLogin/AudioEngine';
import { trackGameEvent } from '@/lib/analytics';

interface Message {
  id: string;
  role: 'user' | 'mentor';
  content: string;
  timestamp: Date;
  mentorType?: MentorType;
}

interface MentorType {
  id: string;
  name: string;
  personality: string;
  avatar: React.ReactNode;
  speciality: string;
  color: string;
}

interface AIMentorSystemProps {
  userLevel?: number;
  subject?: string;
  recentPerformance?: {
    accuracy: number;
    weakAreas: string[];
    strongAreas: string[];
  };
}

const MENTOR_TYPES: MentorType[] = [
  {
    id: 'sage',
    name: 'Sabio Ancestral',
    personality: 'Sabio y paciente, te guía con metáforas y ejemplos profundos',
    avatar: <Brain className="w-8 h-8" />,
    speciality: 'Conceptos profundos y conexiones',
    color: 'from-purple-500 to-purple-600'
  },
  {
    id: 'warrior',
    name: 'Guerrero Estratega',
    personality: 'Directo y motivador, te empuja a superar tus límites',
    avatar: <Target className="w-8 h-8" />,
    speciality: 'Técnicas de estudio y disciplina',
    color: 'from-red-500 to-red-600'
  },
  {
    id: 'scholar',
    name: 'Erudito Analítico',
    personality: 'Detallista y metódico, descompone problemas complejos',
    avatar: <BookOpen className="w-8 h-8" />,
    speciality: 'Análisis detallado y patrones',
    color: 'from-blue-500 to-blue-600'
  },
  {
    id: 'coach',
    name: 'Entrenador Optimista',
    personality: 'Energético y alentador, celebra cada pequeño logro',
    avatar: <TrendingUp className="w-8 h-8" />,
    speciality: 'Motivación y progreso continuo',
    color: 'from-green-500 to-green-600'
  }
];

// Simulated AI responses based on mentor type
const getMentorResponse = (
  mentor: MentorType, 
  userMessage: string, 
  context: any
): string => {
  const responses: Record<string, Record<string, string[]>> = {
    sage: {
      greeting: [
        "Saludos, joven aprendiz. Como las aguas del río moldean la piedra, así el conocimiento moldea la mente.",
        "Bienvenido. Cada pregunta es una puerta hacia la sabiduría infinita."
      ],
      help: [
        "Observa cómo cada concepto se conecta con otro, como una red infinita de conocimiento.",
        "La verdadera comprensión viene no de memorizar, sino de ver las conexiones invisibles."
      ],
      motivation: [
        "Recuerda: incluso el roble más fuerte comenzó como una pequeña semilla.",
        "El camino del conocimiento es largo, pero cada paso te acerca a la iluminación."
      ]
    },
    warrior: {
      greeting: [
        "¡En guardia, guerrero! Hoy conquistaremos nuevos territorios del conocimiento.",
        "¡Listo para la batalla! Cada pregunta vencida es una victoria ganada."
      ],
      help: [
        "¡Ataca el problema desde múltiples ángulos! No te rindas ante el primer obstáculo.",
        "Estrategia y disciplina. Divide y conquista cada concepto."
      ],
      motivation: [
        "¡Eres más fuerte de lo que crees! ¡Sigue luchando!",
        "¡Cada error es una lección! ¡Levántate y ataca de nuevo!"
      ]
    },
    scholar: {
      greeting: [
        "Excelente. Procedamos con el análisis sistemático del conocimiento.",
        "Bienvenido. Examinemos los datos y patrones de tu aprendizaje."
      ],
      help: [
        "Analicemos: este concepto se divide en 3 componentes principales...",
        "Observa el patrón: A→B→C. La lógica subyacente es clara cuando la descomponemos."
      ],
      motivation: [
        "Estadísticamente, tu progreso muestra una mejora del 15%. Continúa así.",
        "Los datos indican que estás cerca del dominio. Mantén el enfoque analítico."
      ]
    },
    coach: {
      greeting: [
        "¡Hey campeón! ¡Qué alegría verte! ¿Listo para brillar hoy?",
        "¡Mi estudiante estrella! ¡Hoy será un día increíble!"
      ],
      help: [
        "¡Genial pregunta! Mira, es más fácil de lo que parece...",
        "¡Me encanta tu curiosidad! Vamos paso a paso, ¡tú puedes!"
      ],
      motivation: [
        "¡WOW! ¡Mira todo lo que has avanzado! ¡Eres increíble!",
        "¡Cada día eres mejor! ¡Sigue así, superestrella!"
      ]
    }
  };
  
  // Simple keyword matching for demo
  const messageType = userMessage.toLowerCase().includes('hola') || 
                     userMessage.toLowerCase().includes('hi') ? 'greeting' :
                     userMessage.toLowerCase().includes('ayuda') || 
                     userMessage.toLowerCase().includes('help') ? 'help' : 'motivation';
  
  const mentorResponses = responses[mentor.id][messageType];
  return mentorResponses[Math.floor(Math.random() * mentorResponses.length)];
};

export default function AIMentorSystem({ 
  userLevel = 1, 
  subject = 'general',
  recentPerformance 
}: AIMentorSystemProps) {
  const { playSound } = useAudio();
  const [selectedMentor, setSelectedMentor] = useState<MentorType>(MENTOR_TYPES[0]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  
  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // Initial greeting
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      const greeting = getMentorResponse(selectedMentor, 'hola', { userLevel, subject });
      setMessages([{
        id: '1',
        role: 'mentor',
        content: greeting,
        timestamp: new Date(),
        mentorType: selectedMentor
      }]);
    }
  }, [isOpen, selectedMentor, userLevel, subject]);
  
  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;
    
    playSound('typing_click');
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);
    
    trackGameEvent('mentor_message_sent', {
      mentorId: selectedMentor.id,
      messageLength: inputValue.length
    });
    
    // Simulate AI response delay
    setTimeout(() => {
      const response = getMentorResponse(selectedMentor, inputValue, {
        userLevel,
        subject,
        recentPerformance
      });
      
      const mentorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'mentor',
        content: response,
        timestamp: new Date(),
        mentorType: selectedMentor
      };
      
      setMessages(prev => [...prev, mentorMessage]);
      setIsTyping(false);
      playSound('notification_epic');
    }, 1500 + Math.random() * 1000);
  };
  
  const handleMentorChange = (mentor: MentorType) => {
    playSound('quest_complete');
    setSelectedMentor(mentor);
    setMessages([]); // Clear chat when changing mentor
    trackGameEvent('mentor_changed', { mentorId: mentor.id });
  };
  
  const handleSpeak = (message: string) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(message);
      utterance.lang = 'es-ES';
      utterance.rate = 0.9;
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      speechSynthesis.speak(utterance);
    }
  };
  
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('es-ES', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };
  
  return (
    <>
      {/* Floating Button */}
      <motion.button
        className="fixed bottom-8 left-8 bg-gradient-to-r from-purple-600 to-purple-700 
          hover:from-purple-700 hover:to-purple-800 text-white rounded-full p-4 
          shadow-lg transition-all transform hover:scale-110 z-40"
        onClick={() => {
          setIsOpen(true);
          playSound('typing_click');
        }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
      >
        <Brain className="w-6 h-6" />
      </motion.button>
      
      {/* Mentor Chat Modal */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsOpen(false)}
          >
            <motion.div
              className="bg-gray-900 rounded-lg w-full max-w-4xl h-[80vh] flex overflow-hidden"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={e => e.stopPropagation()}
            >
              {/* Mentor Selection Sidebar */}
              <div className="w-80 bg-gray-800 p-6 overflow-y-auto">
                <h3 className="text-xl font-bold text-white mb-6">
                  Elige tu Mentor
                </h3>
                
                <div className="space-y-4">
                  {MENTOR_TYPES.map(mentor => (
                    <motion.button
                      key={mentor.id}
                      onClick={() => handleMentorChange(mentor)}
                      className={`w-full p-4 rounded-lg text-left transition-all ${
                        selectedMentor.id === mentor.id
                          ? 'bg-gradient-to-r ' + mentor.color + ' text-white'
                          : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                      }`}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <div className="flex items-start gap-3">
                        <div className={selectedMentor.id === mentor.id ? '' : 'opacity-70'}>
                          {mentor.avatar}
                        </div>
                        <div className="flex-1">
                          <h4 className="font-semibold mb-1">{mentor.name}</h4>
                          <p className="text-sm opacity-90 mb-2">
                            {mentor.personality}
                          </p>
                          <p className="text-xs opacity-80">
                            Especialidad: {mentor.speciality}
                          </p>
                        </div>
                      </div>
                    </motion.button>
                  ))}
                </div>
                
                {/* Performance Summary */}
                {recentPerformance && (
                  <div className="mt-6 bg-gray-700 rounded-lg p-4">
                    <h4 className="text-sm font-semibold text-gray-300 mb-3">
                      Tu Rendimiento
                    </h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Precisión</span>
                        <span className="text-white font-semibold">
                          {recentPerformance.accuracy}%
                        </span>
                      </div>
                      {recentPerformance.weakAreas.length > 0 && (
                        <div>
                          <span className="text-gray-400">Áreas débiles:</span>
                          <div className="mt-1">
                            {recentPerformance.weakAreas.map(area => (
                              <span key={area} className="inline-block bg-red-900/30 
                                text-red-400 text-xs px-2 py-1 rounded mr-1 mb-1">
                                {area}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
              
              {/* Chat Area */}
              <div className="flex-1 flex flex-col">
                {/* Header */}
                <div className={`bg-gradient-to-r ${selectedMentor.color} p-4 flex 
                  items-center justify-between`}>
                  <div className="flex items-center gap-3 text-white">
                    {selectedMentor.avatar}
                    <div>
                      <h3 className="font-bold">{selectedMentor.name}</h3>
                      <p className="text-sm opacity-90">Mentor IA Personalizado</p>
                    </div>
                  </div>
                  
                  <button
                    onClick={() => setIsOpen(false)}
                    className="text-white/70 hover:text-white transition-colors"
                  >
                    <X className="w-6 h-6" />
                  </button>
                </div>
                
                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                  {messages.map(message => (
                    <motion.div
                      key={message.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className={`max-w-[70%] ${
                        message.role === 'user' 
                          ? 'bg-purple-600 text-white' 
                          : 'bg-gray-800 text-gray-100'
                      } rounded-lg p-4`}>
                        {message.role === 'mentor' && (
                          <div className="flex items-center gap-2 mb-2">
                            <div className={`text-${message.mentorType?.color}`}>
                              {message.mentorType?.avatar}
                            </div>
                            <span className="font-semibold text-sm">
                              {message.mentorType?.name}
                            </span>
                          </div>
                        )}
                        
                        <p className="mb-2">{message.content}</p>
                        
                        <div className="flex items-center justify-between">
                          <span className="text-xs opacity-70">
                            {formatTime(message.timestamp)}
                          </span>
                          
                          {message.role === 'mentor' && (
                            <button
                              onClick={() => handleSpeak(message.content)}
                              className="text-xs opacity-70 hover:opacity-100 transition-opacity"
                            >
                              <Volume2 className={`w-4 h-4 ${isSpeaking ? 'text-purple-400' : ''}`} />
                            </button>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                  
                  {isTyping && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="flex items-center gap-2 text-gray-400"
                    >
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span className="text-sm">{selectedMentor.name} está escribiendo...</span>
                    </motion.div>
                  )}
                  
                  <div ref={messagesEndRef} />
                </div>
                
                {/* Input Area */}
                <div className="border-t border-gray-700 p-4">
                  <form 
                    onSubmit={(e) => {
                      e.preventDefault();
                      handleSendMessage();
                    }}
                    className="flex gap-3"
                  >
                    <input
                      type="text"
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      placeholder="Escribe tu pregunta..."
                      className="flex-1 bg-gray-800 text-white px-4 py-3 rounded-lg
                        focus:outline-none focus:ring-2 focus:ring-purple-500"
                      disabled={isTyping}
                    />
                    
                    <button
                      type="submit"
                      disabled={!inputValue.trim() || isTyping}
                      className="bg-gradient-to-r from-purple-600 to-purple-700 
                        hover:from-purple-700 hover:to-purple-800 disabled:from-gray-600 
                        disabled:to-gray-700 text-white px-6 py-3 rounded-lg 
                        transition-all flex items-center gap-2"
                    >
                      <Send className="w-5 h-5" />
                    </button>
                  </form>
                  
                  <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <Sparkles className="w-3 h-3" />
                      Powered by AI
                    </span>
                    <span>
                      Presiona Enter para enviar
                    </span>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}