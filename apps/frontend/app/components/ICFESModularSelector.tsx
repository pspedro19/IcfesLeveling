'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Brain, 
  Book, 
  Globe, 
  Microscope, 
  MessageSquare,
  CheckCircle,
  Info,
  Sparkles,
  Lock,
  ChevronRight
} from 'lucide-react';
import { useAudio } from './PortalLogin/AudioEngine';

interface ICFESModule {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  gradient: string;
  topics: string[];
  required: boolean;
  credits: number;
}

interface ICFESModularSelectorProps {
  onComplete: (selectedModules: string[]) => void;
  minModules?: number;
  maxModules?: number;
  userLevel?: number;
}

const ICFES_MODULES: ICFESModule[] = [
  {
    id: 'matematicas',
    name: 'Matemáticas',
    description: 'Razonamiento cuantitativo y resolución de problemas',
    icon: <Brain className="w-8 h-8" />,
    color: 'text-blue-400',
    gradient: 'from-blue-500 to-blue-600',
    topics: ['Álgebra', 'Geometría', 'Estadística', 'Cálculo'],
    required: true,
    credits: 3
  },
  {
    id: 'lectura_critica',
    name: 'Lectura Crítica',
    description: 'Comprensión e interpretación de textos',
    icon: <Book className="w-8 h-8" />,
    color: 'text-purple-400',
    gradient: 'from-purple-500 to-purple-600',
    topics: ['Comprensión', 'Análisis', 'Inferencia', 'Crítica'],
    required: true,
    credits: 3
  },
  {
    id: 'sociales',
    name: 'Sociales y Ciudadanas',
    description: 'Competencias ciudadanas y conocimientos sociales',
    icon: <Globe className="w-8 h-8" />,
    color: 'text-green-400',
    gradient: 'from-green-500 to-green-600',
    topics: ['Historia', 'Geografía', 'Constitución', 'Economía'],
    required: true,
    credits: 3
  },
  {
    id: 'ciencias',
    name: 'Ciencias Naturales',
    description: 'Biología, química y física aplicadas',
    icon: <Microscope className="w-8 h-8" />,
    color: 'text-yellow-400',
    gradient: 'from-yellow-500 to-yellow-600',
    topics: ['Biología', 'Química', 'Física', 'Ambiente'],
    required: true,
    credits: 3
  },
  {
    id: 'ingles',
    name: 'Inglés',
    description: 'Comprensión y uso del idioma inglés',
    icon: <MessageSquare className="w-8 h-8" />,
    color: 'text-red-400',
    gradient: 'from-red-500 to-red-600',
    topics: ['Grammar', 'Reading', 'Vocabulary', 'Comprehension'],
    required: true,
    credits: 3
  }
];

// Módulos opcionales para el futuro
const OPTIONAL_MODULES: ICFESModule[] = [
  {
    id: 'filosofia',
    name: 'Filosofía',
    description: 'Pensamiento crítico y reflexión filosófica',
    icon: <Brain className="w-8 h-8" />,
    color: 'text-indigo-400',
    gradient: 'from-indigo-500 to-indigo-600',
    topics: ['Lógica', 'Ética', 'Epistemología', 'Estética'],
    required: false,
    credits: 2
  },
  {
    id: 'artes',
    name: 'Artes y Diseño',
    description: 'Apreciación artística y creatividad',
    icon: <Sparkles className="w-8 h-8" />,
    color: 'text-pink-400',
    gradient: 'from-pink-500 to-pink-600',
    topics: ['Historia del Arte', 'Diseño', 'Música', 'Expresión'],
    required: false,
    credits: 2
  }
];

export default function ICFESModularSelector({ 
  onComplete, 
  minModules = 5, 
  maxModules = 5,
  userLevel = 1 
}: ICFESModularSelectorProps) {
  const { playSound } = useAudio();
  const [selectedModules, setSelectedModules] = useState<string[]>(
    ICFES_MODULES.filter(m => m.required).map(m => m.id)
  );
  const [showDetails, setShowDetails] = useState<string | null>(null);
  const [confirmSelection, setConfirmSelection] = useState(false);
  
  const allModules = [...ICFES_MODULES, ...(userLevel >= 10 ? OPTIONAL_MODULES : [])];
  const totalCredits = selectedModules.reduce((acc, id) => {
    const module = allModules.find(m => m.id === id);
    return acc + (module?.credits || 0);
  }, 0);
  
  const handleModuleToggle = (moduleId: string) => {
    const module = allModules.find(m => m.id === moduleId);
    if (!module) return;
    
    if (module.required) {
      playSound('notification_epic');
      return;
    }
    
    setSelectedModules(prev => {
      if (prev.includes(moduleId)) {
        playSound('damage_hit');
        return prev.filter(id => id !== moduleId);
      } else {
        if (prev.length >= maxModules) {
          playSound('glitch');
          return prev;
        }
        playSound('quest_complete');
        return [...prev, moduleId];
      }
    });
  };
  
  const handleConfirm = () => {
    if (selectedModules.length >= minModules) {
      playSound('level_up');
      onComplete(selectedModules);
    }
  };
  
  const getModuleStatus = (moduleId: string) => {
    const module = allModules.find(m => m.id === moduleId);
    if (!module) return 'locked';
    
    if (module.required) return 'required';
    if (selectedModules.includes(moduleId)) return 'selected';
    if (selectedModules.length >= maxModules) return 'disabled';
    return 'available';
  };
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-6xl mx-auto"
      >
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-4 font-cinzel">
            Selección de Módulos ICFES
          </h1>
          <p className="text-xl text-purple-200 mb-2">
            Personaliza tu experiencia de aprendizaje
          </p>
          <div className="flex items-center justify-center gap-4 text-sm text-gray-300">
            <span className="flex items-center gap-2">
              <div className="w-4 h-4 bg-purple-500 rounded" />
              Obligatorios
            </span>
            <span className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-500 rounded" />
              Seleccionados
            </span>
            <span className="flex items-center gap-2">
              <div className="w-4 h-4 bg-gray-600 rounded" />
              Opcionales
            </span>
          </div>
        </div>
        
        {/* Progress Bar */}
        <div className="bg-gray-800 rounded-lg p-4 mb-8">
          <div className="flex justify-between items-center mb-2">
            <span className="text-white font-semibold">
              Módulos Seleccionados: {selectedModules.length} / {maxModules}
            </span>
            <span className="text-purple-400 font-semibold">
              {totalCredits} Créditos
            </span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-3">
            <motion.div
              className="h-full bg-gradient-to-r from-purple-500 to-purple-600 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${(selectedModules.length / maxModules) * 100}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
        </div>
        
        {/* Modules Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {allModules.map((module, index) => {
            const status = getModuleStatus(module.id);
            const isSelected = selectedModules.includes(module.id);
            
            return (
              <motion.div
                key={module.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
                className="relative"
              >
                <motion.div
                  className={`
                    relative overflow-hidden rounded-lg cursor-pointer
                    transition-all duration-300 transform hover:scale-105
                    ${status === 'required' ? 'ring-2 ring-purple-500' : ''}
                    ${status === 'selected' ? 'ring-2 ring-green-500' : ''}
                    ${status === 'disabled' ? 'opacity-50 cursor-not-allowed' : ''}
                  `}
                  onClick={() => handleModuleToggle(module.id)}
                  whileHover={status !== 'disabled' ? { y: -5 } : {}}
                  whileTap={status !== 'disabled' ? { scale: 0.98 } : {}}
                >
                  <div className={`
                    bg-gradient-to-br ${module.gradient} p-6
                    ${isSelected ? 'opacity-100' : 'opacity-80'}
                  `}>
                    {/* Status Badge */}
                    <div className="absolute top-3 right-3">
                      {status === 'required' && (
                        <Lock className="w-5 h-5 text-white/70" />
                      )}
                      {status === 'selected' && (
                        <CheckCircle className="w-6 h-6 text-white" />
                      )}
                    </div>
                    
                    {/* Module Content */}
                    <div className="text-white mb-4">
                      {module.icon}
                    </div>
                    
                    <h3 className="text-xl font-bold text-white mb-2">
                      {module.name}
                    </h3>
                    
                    <p className="text-white/80 text-sm mb-4">
                      {module.description}
                    </p>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-white/60">
                        {module.credits} créditos
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowDetails(module.id);
                          playSound('typing_click');
                        }}
                        className="text-white/80 hover:text-white transition-colors"
                      >
                        <Info className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  
                  {/* Overlay for non-required modules */}
                  {!module.required && !isSelected && (
                    <div className="absolute inset-0 bg-black/30 flex items-center justify-center">
                      <span className="text-white font-semibold">
                        Click para agregar
                      </span>
                    </div>
                  )}
                </motion.div>
              </motion.div>
            );
          })}
        </div>
        
        {/* Confirm Button */}
        <motion.div
          className="flex justify-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <button
            onClick={() => setConfirmSelection(true)}
            disabled={selectedModules.length < minModules}
            className={`
              px-8 py-4 rounded-lg font-bold text-lg
              transition-all duration-300 transform hover:scale-105
              flex items-center gap-3
              ${selectedModules.length >= minModules
                ? 'bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white'
                : 'bg-gray-700 text-gray-400 cursor-not-allowed'
              }
            `}
          >
            Confirmar Selección
            <ChevronRight className="w-5 h-5" />
          </button>
        </motion.div>
      </motion.div>
      
      {/* Module Details Modal */}
      <AnimatePresence>
        {showDetails && (
          <motion.div
            className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowDetails(null)}
          >
            <motion.div
              className="bg-gray-900 rounded-lg p-6 max-w-md w-full"
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              onClick={(e) => e.stopPropagation()}
            >
              {(() => {
                const module = allModules.find(m => m.id === showDetails);
                if (!module) return null;
                
                return (
                  <>
                    <div className={`${module.color} mb-4`}>
                      {module.icon}
                    </div>
                    
                    <h3 className="text-2xl font-bold text-white mb-2">
                      {module.name}
                    </h3>
                    
                    <p className="text-gray-300 mb-4">
                      {module.description}
                    </p>
                    
                    <div className="mb-4">
                      <h4 className="text-lg font-semibold text-white mb-2">
                        Temas incluidos:
                      </h4>
                      <div className="grid grid-cols-2 gap-2">
                        {module.topics.map(topic => (
                          <div
                            key={topic}
                            className="bg-gray-800 rounded px-3 py-1 text-sm text-gray-300"
                          >
                            {topic}
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-400">
                        {module.required ? 'Módulo Obligatorio' : 'Módulo Opcional'}
                      </span>
                      <span className="text-purple-400 font-semibold">
                        {module.credits} créditos
                      </span>
                    </div>
                    
                    <button
                      onClick={() => setShowDetails(null)}
                      className="w-full mt-6 bg-gray-700 hover:bg-gray-600 text-white
                        font-semibold py-2 rounded-lg transition-colors"
                    >
                      Cerrar
                    </button>
                  </>
                );
              })()}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Confirmation Modal */}
      <AnimatePresence>
        {confirmSelection && (
          <motion.div
            className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="bg-gray-900 rounded-lg p-6 max-w-md w-full"
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
            >
              <Sparkles className="w-16 h-16 text-purple-400 mx-auto mb-4" />
              
              <h3 className="text-2xl font-bold text-white text-center mb-4">
                ¿Confirmar Selección?
              </h3>
              
              <div className="bg-gray-800 rounded-lg p-4 mb-6">
                <h4 className="text-lg font-semibold text-white mb-3">
                  Módulos seleccionados:
                </h4>
                <div className="space-y-2">
                  {selectedModules.map(id => {
                    const module = allModules.find(m => m.id === id);
                    if (!module) return null;
                    
                    return (
                      <div key={id} className="flex items-center gap-3">
                        <div className={module.color}>
                          <CheckCircle className="w-5 h-5" />
                        </div>
                        <span className="text-gray-300">{module.name}</span>
                        <span className="text-gray-500 text-sm ml-auto">
                          {module.credits} créditos
                        </span>
                      </div>
                    );
                  })}
                </div>
                
                <div className="mt-4 pt-4 border-t border-gray-700">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">Total:</span>
                    <span className="text-xl font-bold text-purple-400">
                      {totalCredits} créditos
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="flex gap-3">
                <button
                  onClick={() => setConfirmSelection(false)}
                  className="flex-1 bg-gray-700 hover:bg-gray-600 text-white
                    font-semibold py-3 rounded-lg transition-colors"
                >
                  Modificar
                </button>
                
                <button
                  onClick={handleConfirm}
                  className="flex-1 bg-gradient-to-r from-purple-600 to-purple-700
                    hover:from-purple-700 hover:to-purple-800 text-white font-bold
                    py-3 rounded-lg transition-all transform hover:scale-105"
                >
                  Confirmar
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}