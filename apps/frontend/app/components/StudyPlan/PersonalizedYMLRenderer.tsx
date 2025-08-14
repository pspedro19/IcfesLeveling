'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BookOpen, Play, Target, Clock, TrendingUp, AlertCircle,
  CheckCircle, XCircle, Info, Video, FileText, Activity,
  Calendar, Star, Zap, ChevronDown, ChevronRight, Eye, EyeOff
} from 'lucide-react';

// Importar el componente de YouTube
import YouTubeVideoRenderer from './YouTubeVideoRenderer';

// Importar el sistema de diseño
import {
  buildButtonClasses,
  buildCardClasses,
  buildBadgeClasses,
  buildAlertClasses,
  buildSpinnerClasses,
  buildSkeletonClasses,
  spacingClasses,
  typographyClasses,
  animationClasses,
  cn
} from '../../utils/component-classes';

// Interfaces para el YML
interface YMLData {
  plan_id: string;
  subject: string;
  user_profile: {
    learning_style: string;
    pace: string;
    confidence_level: string;
    weak_topics: string[];
    strong_topics: string[];
  };
  diagnostic_context: {
    test_date: string;
    overall_score: number;
    mistakes_analysis: Array<{
      topic: string;
      question_type: string;
      user_answer: string;
      correct_answer: string;
      explanation: string;
      difficulty: string;
    }>;
  };
  learning_path: {
    total_modules: number;
    estimated_duration: string;
    difficulty_progression: string;
    modules: Array<{
      module_number: number;
      title: string;
      description: string;
      topics: string[];
      difficulty: string;
      estimated_time: string;
      resources: {
        videos: string[];
        exercises: string[];
        materials: string[];
      };
      ai_explanation: string;
      personalization_rules: string[];
    }>;
  };
  adaptive_rules: {
    success_threshold: number;
    failure_threshold: number;
    difficulty_adjustment: string;
    repetition_strategy: string;
  };
}

interface PersonalizedYMLRendererProps {
  userId: string;
  subject: string;
  onModuleComplete?: (moduleId: number) => void;
  onLessonStart?: (moduleId: number, lessonId: string) => void;
}

const PersonalizedYMLRenderer: React.FC<PersonalizedYMLRendererProps> = ({
  userId,
  subject,
  onModuleComplete,
  onLessonStart
}) => {
  const [ymlData, setYmlData] = useState<YMLData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentModule, setCurrentModule] = useState(0);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});
  const [showMistakeContext, setShowMistakeContext] = useState<Record<string, boolean>>({});
  const [showVideoSection, setShowVideoSection] = useState(false);
  const [selectedVideos, setSelectedVideos] = useState<any[]>([]);

  useEffect(() => {
    fetchUserYML();
  }, [userId, subject]);

  const fetchUserYML = async () => {
    try {
      setLoading(true);
      
      // Simular fetch de YML desde el backend
      // En producción, esto vendría de la API
      const mockYMLData: YMLData = {
        plan_id: `plan_${userId}_${subject}`,
        subject: subject,
        user_profile: {
          learning_style: "Visual y Kinestésico",
          pace: "Moderado",
          confidence_level: "Media",
          weak_topics: ["Álgebra", "Geometría", "Trigonometría"],
          strong_topics: ["Aritmética", "Estadística"]
        },
        diagnostic_context: {
          test_date: "2024-01-15",
          overall_score: 65,
          mistakes_analysis: [
            {
              topic: "Álgebra",
              question_type: "Ecuaciones cuadráticas",
              user_answer: "x = 2",
              correct_answer: "x = 2, x = -3",
              explanation: "Olvidaste considerar ambas raíces de la ecuación cuadrática",
              difficulty: "Intermedio"
            },
            {
              topic: "Geometría",
              question_type: "Teorema de Pitágoras",
              user_answer: "5",
              correct_answer: "13",
              explanation: "Aplicaste incorrectamente la fórmula a² + b² = c²",
              difficulty: "Básico"
            }
          ]
        },
        learning_path: {
          total_modules: 8,
          estimated_duration: "6 semanas",
          difficulty_progression: "Gradual",
          modules: [
            {
              module_number: 1,
              title: "Fundamentos de Álgebra",
              description: "Repaso de conceptos básicos de álgebra para fortalecer la base",
              topics: ["Expresiones algebraicas", "Ecuaciones lineales", "Factorización"],
              difficulty: "Básico",
              estimated_time: "2 horas",
              resources: {
                videos: ["video_algebra_basico.mp4"],
                exercises: ["ejercicio_ecuaciones.pdf"],
                materials: ["guia_algebra.pdf"]
              },
              ai_explanation: "Este módulo está diseñado específicamente para ti porque en el diagnóstico tuviste dificultades con ecuaciones cuadráticas. Empezamos con lo básico para construir una base sólida.",
              personalization_rules: ["Repetición espaciada", "Ejemplos visuales", "Práctica incremental"]
            },
            {
              module_number: 2,
              title: "Ecuaciones Cuadráticas",
              description: "Aplicación práctica de métodos de resolución de ecuaciones cuadráticas",
              topics: ["Fórmula cuadrática", "Completar el cuadrado", "Factorización"],
              difficulty: "Intermedio",
              estimated_time: "3 horas",
              resources: {
                videos: ["video_cuadraticas.mp4"],
                exercises: ["ejercicio_cuadraticas.pdf"],
                materials: ["guia_cuadraticas.pdf"]
              },
              ai_explanation: "Aquí es donde tuviste el error principal. Te proporciono múltiples métodos de resolución y práctica específica para este tipo de problemas.",
              personalization_rules: ["Múltiples métodos", "Práctica intensiva", "Retroalimentación inmediata"]
            }
          ]
        },
        adaptive_rules: {
          success_threshold: 80,
          failure_threshold: 60,
          difficulty_adjustment: "Dinámico",
          repetition_strategy: "Espaciada"
        }
      };

      // Simular delay de red
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setYmlData(mockYMLData);
      
      // Guardar en localStorage para offline
      localStorage.setItem(`yml_${userId}_${subject}`, JSON.stringify(mockYMLData));
      
    } catch (err) {
      setError('Error cargando el plan de estudio personalizado');
      console.error('Error fetching YML:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [sectionId]: !prev[sectionId]
    }));
  };

  const toggleMistakeContext = (topic: string) => {
    setShowMistakeContext(prev => ({
      ...prev,
      [topic]: !prev[topic]
    }));
  };

  const handleModuleComplete = (moduleId: number) => {
    onModuleComplete?.(moduleId);
    // Lógica adicional para marcar módulo como completado
  };

  const handleLessonStart = (moduleId: number, lessonId: string) => {
    onLessonStart?.(moduleId, lessonId);
    // Lógica adicional para iniciar lección
  };

  const handleVideoSelect = (video: any) => {
    console.log('Video seleccionado:', video);
    // Aquí se puede agregar lógica adicional para el video seleccionado
  };

  const handleVideoComplete = (video: any, progress: number) => {
    console.log('Video completado:', video, 'Progreso:', progress);
    // Aquí se puede agregar lógica para marcar el video como completado
  };

  const toggleVideoSection = () => {
    setShowVideoSection(!showVideoSection);
  };

  // Loading State
  if (loading) {
    return (
      <div className={cn(spacingClasses.container, "py-8")}>
        <div className="space-y-6">
          {/* Header Skeleton */}
          <div className="space-y-4">
            <div className={buildSkeletonClasses('title', "w-1/3")} />
            <div className={buildSkeletonClasses('text', "w-1/2")} />
          </div>
          
          {/* Profile Skeleton */}
          <div className={buildCardClasses({ size: 'md' })}>
            <div className="space-y-4">
              <div className={buildSkeletonClasses('title', "w-1/4")} />
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[1, 2, 3].map(i => (
                  <div key={i} className={buildSkeletonClasses('card', "h-20")} />
                ))}
              </div>
            </div>
          </div>
          
          {/* Modules Skeleton */}
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className={buildCardClasses({ size: 'lg' })}>
                <div className="space-y-4">
                  <div className={buildSkeletonClasses('title', "w-1/3")} />
                  <div className={buildSkeletonClasses('text', "w-full")} />
                  <div className={buildSkeletonClasses('text', "w-2/3")} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Error State
  if (error && !ymlData) {
    return (
      <div className={cn(spacingClasses.container, "py-8")}>
        <div className={buildAlertClasses({ variant: 'error', size: 'lg' })}>
          <div className="flex items-center space-x-3">
            <AlertCircle className="h-6 w-6 text-error" />
            <div>
              <h3 className="font-semibold">Error al cargar el plan</h3>
              <p className="text-sm">{error}</p>
            </div>
          </div>
          <button
            onClick={fetchUserYML}
            className={buildButtonClasses({ 
              variant: 'outline', 
              size: 'sm',
              className: "mt-3"
            })}
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  // No Data State
  if (!ymlData) {
    return (
      <div className={cn(spacingClasses.container, "py-8")}>
        <div className={buildCardClasses({ size: 'lg', variant: 'outlined' })}>
          <div className="text-center space-y-4">
            <BookOpen className="h-16 w-16 text-neutral-400 mx-auto" />
            <h3 className={typographyClasses.heading.h3}>No hay plan disponible</h3>
            <p className="text-neutral-600">
              No se encontró un plan de estudio personalizado para {subject}.
            </p>
            <button
              onClick={fetchUserYML}
              className={buildButtonClasses({ variant: 'primary' })}
            >
              Generar Plan
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn(spacingClasses.container, "py-8")}>
      <motion.div 
        className="space-y-8"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        {/* Header del Plan */}
        <motion.div 
          className="text-center space-y-4"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1, duration: 0.5 }}
        >
          <h1 className={cn(typographyClasses.heading.h1, "text-primary")}>
            Plan de Estudio Personalizado
          </h1>
          <p className={cn(typographyClasses.body.large, "text-neutral-600 max-w-2xl mx-auto")}>
            Tu ruta de aprendizaje única para {subject}, diseñada específicamente 
            basada en tu diagnóstico y perfil de aprendizaje.
          </p>
          <div className="flex items-center justify-center space-x-4 text-sm text-neutral-500">
            <span className="flex items-center space-x-1">
              <Calendar className="h-4 w-4" />
              <span>Generado el {new Date(ymlData.diagnostic_context.test_date).toLocaleDateString()}</span>
            </span>
            <span className="flex items-center space-x-1">
              <Clock className="h-4 w-4" />
              <span>{ymlData.learning_path.estimated_duration}</span>
            </span>
            <span className="flex items-center space-x-1">
              <Target className="h-4 w-4" />
              <span>{ymlData.learning_path.total_modules} módulos</span>
            </span>
          </div>
        </motion.div>

        {/* Perfil de Personalización */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <div className={buildCardClasses({ size: 'lg', variant: 'elevated' })}>
            <div className="space-y-6">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <Star className="h-6 w-6 text-primary" />
                </div>
                <h2 className={typographyClasses.heading.h3}>Tu Perfil de Aprendizaje</h2>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <h4 className="font-semibold text-neutral-700">Estilo de Aprendizaje</h4>
                  <p className="text-sm text-neutral-600">{ymlData.user_profile.learning_style}</p>
                </div>
                <div className="space-y-2">
                  <h4 className="font-semibold text-neutral-700">Ritmo</h4>
                  <p className="text-sm text-neutral-600">{ymlData.user_profile.pace}</p>
                </div>
                <div className="space-y-2">
                  <h4 className="font-semibold text-neutral-700">Nivel de Confianza</h4>
                  <p className="text-sm text-neutral-600">{ymlData.user_profile.confidence_level}</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-3">
                  <h4 className="font-semibold text-neutral-700 flex items-center space-x-2">
                    <XCircle className="h-5 w-5 text-error" />
                    <span>Temas Débiles</span>
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {ymlData.user_profile.weak_topics.map((topic, index) => (
                      <span
                        key={index}
                        className={buildBadgeClasses({ variant: 'error', size: 'sm' })}
                      >
                        {topic}
                      </span>
                    ))}
                  </div>
                </div>
                
                <div className="space-y-3">
                  <h4 className="font-semibold text-neutral-700 flex items-center space-x-2">
                    <CheckCircle className="h-5 w-5 text-success" />
                    <span>Temas Fuertes</span>
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {ymlData.user_profile.strong_topics.map((topic, index) => (
                      <span
                        key={index}
                        className={buildBadgeClasses({ variant: 'success', size: 'sm' })}
                      >
                        {topic}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Contexto del Diagnóstico */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
        >
          <div className={buildCardClasses({ size: 'lg', variant: 'outlined' })}>
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-info/10 rounded-lg">
                    <Info className="h-6 w-6 text-info" />
                  </div>
                  <h2 className={typographyClasses.heading.h3}>Contexto del Diagnóstico</h2>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-primary">
                    {ymlData.diagnostic_context.overall_score}%
                  </div>
                  <div className="text-sm text-neutral-500">Puntuación General</div>
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="font-semibold text-neutral-700">Análisis de Errores</h4>
                {ymlData.diagnostic_context.mistakes_analysis.map((mistake, index) => (
                  <motion.div
                    key={index}
                    className="border border-neutral-200 rounded-lg p-4 space-y-3"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 * index, duration: 0.3 }}
                  >
                    <div className="flex items-center justify-between">
                      <h5 className="font-medium text-neutral-800">{mistake.topic}</h5>
                      <span className={buildBadgeClasses({ 
                        variant: mistake.difficulty === 'Básico' ? 'warning' : 'primary',
                        size: 'sm'
                      })}>
                        {mistake.difficulty}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium text-neutral-600">Tu respuesta:</span>
                        <div className="mt-1 p-2 bg-error/10 border border-error/20 rounded text-error">
                          {mistake.user_answer}
                        </div>
                      </div>
                      <div>
                        <span className="font-medium text-neutral-600">Respuesta correcta:</span>
                        <div className="mt-1 p-2 bg-success/10 border border-success/20 rounded text-success">
                          {mistake.correct_answer}
                        </div>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <button
                        onClick={() => toggleMistakeContext(mistake.topic)}
                        className="flex items-center space-x-2 text-sm text-primary hover:text-primary/80 transition-colors"
                      >
                        {showMistakeContext[mistake.topic] ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                        <span>
                          {showMistakeContext[mistake.topic] ? 'Ocultar' : 'Ver'} explicación
                        </span>
                      </button>
                      
                      <AnimatePresence>
                        {showMistakeContext[mistake.topic] && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            transition={{ duration: 0.3 }}
                            className="p-3 bg-neutral-50 rounded border-l-4 border-primary/30"
                          >
                            <p className="text-sm text-neutral-700">{mistake.explanation}</p>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </motion.div>

        {/* Módulos de Aprendizaje */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.5 }}
        >
          <div className="space-y-6">
            <div className="text-center">
              <h2 className={typographyClasses.heading.h2}>Tu Ruta de Aprendizaje</h2>
              <p className="text-neutral-600 mt-2">
                Módulos personalizados diseñados para abordar tus áreas de mejora
              </p>
            </div>

            <div className="space-y-4">
              {ymlData.learning_path.modules.map((module, index) => (
                <motion.div
                  key={module.module_number}
                  className={buildCardClasses({ 
                    size: 'lg', 
                    variant: 'interactive',
                    className: "group"
                  })}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 * index, duration: 0.4 }}
                  whileHover={{ y: -2 }}
                >
                  <div className="space-y-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <div className="flex items-center justify-center w-8 h-8 bg-primary text-white rounded-full text-sm font-bold">
                            {module.module_number}
                          </div>
                          <h3 className={typographyClasses.heading.h4}>{module.title}</h3>
                        </div>
                        
                        <p className="text-neutral-600 mb-3">{module.description}</p>
                        
                        <div className="flex flex-wrap gap-2 mb-3">
                          {module.topics.map((topic, topicIndex) => (
                            <span
                              key={topicIndex}
                              className={buildBadgeClasses({ variant: 'neutral', size: 'sm' })}
                            >
                              {topic}
                            </span>
                          ))}
                        </div>

                        <div className="flex items-center space-x-4 text-sm text-neutral-500">
                          <span className="flex items-center space-x-1">
                            <Clock className="h-4 w-4" />
                            <span>{module.estimated_time}</span>
                          </span>
                          <span className={buildBadgeClasses({ 
                            variant: module.difficulty === 'Básico' ? 'success' : 
                                   module.difficulty === 'Intermedio' ? 'warning' : 'error',
                            size: 'sm'
                          })}>
                            {module.difficulty}
                          </span>
                        </div>
                      </div>

                      <button
                        onClick={() => toggleSection(`module-${module.module_number}`)}
                        className="p-2 text-neutral-400 hover:text-neutral-600 transition-colors"
                      >
                        {expandedSections[`module-${module.module_number}`] ? (
                          <ChevronDown className="h-5 w-5" />
                        ) : (
                          <ChevronRight className="h-5 w-5" />
                        )}
                      </button>
                    </div>

                    <AnimatePresence>
                      {expandedSections[`module-${module.module_number}`] && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          transition={{ duration: 0.3 }}
                          className="space-y-4 pt-4 border-t border-neutral-200"
                        >
                          {/* Explicación AI */}
                          <div className="p-4 bg-primary/5 rounded-lg border border-primary/20">
                            <div className="flex items-center space-x-2 mb-2">
                              <Zap className="h-5 w-5 text-primary" />
                              <h5 className="font-semibold text-primary">Explicación Personalizada</h5>
                            </div>
                            <p className="text-sm text-neutral-700">{module.ai_explanation}</p>
                          </div>

                          {/* Recursos */}
                          <div className="space-y-3">
                            <h5 className="font-semibold text-neutral-700">Recursos Disponibles</h5>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                              {module.resources.videos.length > 0 && (
                                <div className="flex items-center space-x-2 p-3 bg-neutral-50 rounded border">
                                  <Video className="h-4 w-4 text-primary" />
                                  <span className="text-sm">{module.resources.videos.length} videos</span>
                                </div>
                              )}
                              {module.resources.exercises.length > 0 && (
                                <div className="flex items-center space-x-2 p-3 bg-neutral-50 rounded border">
                                  <FileText className="h-4 w-4 text-secondary" />
                                  <span className="text-sm">{module.resources.exercises.length} ejercicios</span>
                                </div>
                              )}
                              {module.resources.materials.length > 0 && (
                                <div className="flex items-center space-x-2 p-3 bg-neutral-50 rounded border">
                                  <BookOpen className="h-4 w-4 text-accent" />
                                  <span className="text-sm">{module.resources.materials.length} materiales</span>
                                </div>
                              )}
                            </div>
                          </div>

                          {/* Reglas de Personalización */}
                          <div className="space-y-3">
                            <h5 className="font-semibold text-neutral-700">Reglas de Personalización</h5>
                            <div className="space-y-2">
                              {module.personalization_rules.map((rule, ruleIndex) => (
                                <div key={ruleIndex} className="flex items-center space-x-2 text-sm">
                                  <div className="w-2 h-2 bg-primary rounded-full" />
                                  <span className="text-neutral-600">{rule}</span>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Acciones */}
                          <div className="flex space-x-3 pt-3">
                            <button
                              onClick={() => handleLessonStart(module.module_number, `lesson-${module.module_number}`)}
                              className={buildButtonClasses({ 
                                variant: 'primary', 
                                size: 'sm',
                                className: "flex items-center space-x-2"
                              })}
                            >
                              <Play className="h-4 w-4" />
                              <span>Iniciar Lección</span>
                            </button>
                            
                            <button
                              onClick={() => handleModuleComplete(module.module_number)}
                              className={buildButtonClasses({ 
                                variant: 'outline', 
                                size: 'sm',
                                className: "flex items-center space-x-2"
                              })}
                            >
                              <CheckCircle className="h-4 w-4" />
                              <span>Marcar Completado</span>
                            </button>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Sección de Videos de YouTube */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.5 }}
        >
          <div className={buildCardClasses({ size: 'lg', variant: 'elevated' })}>
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    <Video className="h-6 w-6 text-primary" />
                  </div>
                  <h2 className={typographyClasses.heading.h3}>Videos Educativos Personalizados</h2>
                </div>
                <button
                  onClick={toggleVideoSection}
                  className={buildButtonClasses({ 
                    variant: 'outline', 
                    size: 'sm',
                    className: "flex items-center space-x-2"
                  })}
                >
                  {showVideoSection ? (
                    <>
                      <EyeOff className="h-4 w-4" />
                      <span>Ocultar Videos</span>
                    </>
                  ) : (
                    <>
                      <Video className="h-4 w-4" />
                      <span>Ver Videos</span>
                    </>
                  )}
                </button>
              </div>
              
              <AnimatePresence>
                {showVideoSection && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <YouTubeVideoRenderer
                      videos={[]} // Se cargarán desde la API
                      subject={subject}
                      weakTopics={ymlData.user_profile.weak_topics}
                      strongTopics={ymlData.user_profile.strong_topics}
                      learningStyle={ymlData.user_profile.learning_style}
                      onVideoSelect={handleVideoSelect}
                      onVideoComplete={handleVideoComplete}
                      showRecommendations={true}
                      maxVideos={15}
                    />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </motion.div>

        {/* Reglas de Adaptación */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.5 }}
        >
          <div className={buildCardClasses({ size: 'lg', variant: 'elevated' })}>
            <div className="space-y-6">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-secondary/10 rounded-lg">
                  <TrendingUp className="h-6 w-6 text-secondary" />
                </div>
                <h2 className={typographyClasses.heading.h3}>Reglas de Adaptación</h2>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <h4 className="font-semibold text-neutral-700">Umbrales de Éxito</h4>
                    <div className="flex items-center space-x-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-success">
                          {ymlData.adaptive_rules.success_threshold}%
                        </div>
                        <div className="text-sm text-neutral-500">Éxito</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-error">
                          {ymlData.adaptive_rules.failure_threshold}%
                        </div>
                        <div className="text-sm text-neutral-500">Fracaso</div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <h4 className="font-semibold text-neutral-700">Ajuste de Dificultad</h4>
                    <p className="text-sm text-neutral-600">{ymlData.adaptive_rules.difficulty_adjustment}</p>
                  </div>
                </div>
                
                <div className="space-y-4">
                  <div className="space-y-2">
                    <h4 className="font-semibold text-neutral-700">Estrategia de Repetición</h4>
                    <p className="text-sm text-neutral-600">{ymlData.adaptive_rules.repetition_strategy}</p>
                  </div>
                  
                  <div className="space-y-2">
                    <h4 className="font-semibold text-neutral-700">Progresión de Dificultad</h4>
                    <p className="text-sm text-neutral-600">{ymlData.learning_path.difficulty_progression}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
};

export default PersonalizedYMLRenderer;
