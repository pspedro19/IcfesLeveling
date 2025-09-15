'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { getImageUrl } from '@/lib/config';
import { 
  ChevronLeft, 
  ChevronRight, 
  Image as ImageIcon,
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  Target
} from 'lucide-react';

interface MultimediaOption {
  texto?: string;
  imagen?: string;
}

interface MultimediaQuestion {
  id: string;
  pregunta_texto?: string;
  pregunta_imagen?: string;
  opcion_a_texto?: string;
  opcion_a_imagen?: string;
  opcion_b_texto?: string;
  opcion_b_imagen?: string;
  opcion_c_texto?: string;
  opcion_c_imagen?: string;
  opcion_d_texto?: string;
  opcion_d_imagen?: string;
  respuesta_correcta: string;
  difficulty?: number;
  explanation?: string;
  hint?: string;
}

interface MultimediaQuestionProps {
  question: MultimediaQuestion;
  questionNumber: number;
  totalQuestions: number;
  selectedAnswer?: string;
  onAnswerSelect: (answer: string) => void;
  onNext: () => void;
  onPrevious: () => void;
  timeRemaining?: number;
  showExplanation?: boolean;
  isAnswered?: boolean;
}

export default function MultimediaQuestion({
  question,
  questionNumber,
  totalQuestions,
  selectedAnswer,
  onAnswerSelect,
  onNext,
  onPrevious,
  timeRemaining,
  showExplanation = false,
  isAnswered = false
}: MultimediaQuestionProps) {
  const [imageLoading, setImageLoading] = useState<Record<string, boolean>>({});
  const [imageError, setImageError] = useState<Record<string, boolean>>({});

  // Opciones disponibles
  const options: Record<string, MultimediaOption> = {
    'a': { texto: question.opcion_a_texto, imagen: question.opcion_a_imagen },
    'b': { texto: question.opcion_b_texto, imagen: question.opcion_b_imagen },
    'c': { texto: question.opcion_c_texto, imagen: question.opcion_c_imagen },
    'd': { texto: question.opcion_d_texto, imagen: question.opcion_d_imagen }
  };

  const handleImageLoad = (imageKey: string) => {
    setImageLoading(prev => ({ ...prev, [imageKey]: false }));
  };

  const handleImageError = (imageKey: string) => {
    setImageLoading(prev => ({ ...prev, [imageKey]: false }));
    setImageError(prev => ({ ...prev, [imageKey]: true }));
  };

  const renderContent = (texto?: string, imagen?: string, contentKey?: string) => {
    const elements = [] as React.ReactNode[];

    // Si el texto contiene una ruta de imagen en formato "[Imagen: /ruta.png]"
    // o una ruta directa a /mathimg/... mostramos la imagen y ocultamos el texto.
    if (!imagen && texto) {
      const trimmed = texto.trim();
      const bracketMatch = trimmed.match(/^\[(?:Imagen|Image)\s*:\s*(.*?)\]$/i);
      const urlMatch = trimmed.match(/(\/(?:mathimg|images|img)[^\s\]]*\.(?:png|jpg|jpeg|gif))/i);
      if (bracketMatch && bracketMatch[1]) {
        imagen = bracketMatch[1].trim();
        texto = undefined;
      } else if (urlMatch && urlMatch[1]) {
        imagen = urlMatch[1].trim();
        texto = undefined;
      }
    }

    // Validar y construir URL completa para la imagen si es necesario
    if (imagen && imagen !== 'No Aplica' && imagen.trim() !== '') {
      // Usar la función de configuración dinámica
      imagen = getImageUrl(imagen);
    } else {
      imagen = undefined; // Limpieza: no intentar cargar imágenes inválidas
    }

    // Renderizar imagen si existe
    if (imagen) {
      elements.push(
        <div key={`${contentKey}-image`} className="mb-4">
          {imageLoading[contentKey || ''] && (
            <div className="flex items-center justify-center h-48 bg-gray-200 rounded-lg">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
            </div>
          )}
          {imageError[contentKey || ''] ? (
            <div className="flex items-center justify-center h-48 bg-gray-200 rounded-lg text-gray-500">
              <ImageIcon className="w-8 h-8 mr-2" />
              Error al cargar imagen
            </div>
          ) : (
            <img
              src={imagen}
              alt="Contenido multimedia"
              className="max-w-full h-auto rounded-lg shadow-lg"
              onLoad={() => handleImageLoad(contentKey || '')}
              onError={() => handleImageError(contentKey || '')}
              style={{ display: imageLoading[contentKey || ''] ? 'none' : 'block' }}
            />
          )}
        </div>
      );
    }

    // Renderizar texto si existe
    if (texto) {
      elements.push(
        <div key={`${contentKey}-text`} className="mb-4">
          <p className="text-lg text-gray-800 leading-relaxed">{texto}</p>
        </div>
      );
    }

    return elements;
  };

  const getOptionState = (optionKey: string) => {
    if (!isAnswered) return 'default';
    const keyLower = optionKey.toLowerCase();
    const correctLower = (question.respuesta_correcta || '').toLowerCase();
    const selectedLower = (selectedAnswer || '').toLowerCase();
    if (keyLower === correctLower) return 'correct';
    if (keyLower === selectedLower && keyLower !== correctLower) return 'incorrect';
    return 'default';
  };

  const getOptionStyles = (optionKey: string) => {
    const state = getOptionState(optionKey);
    const isSelected = (selectedAnswer || '').toLowerCase() === optionKey.toLowerCase();

    const baseStyles = "w-full p-4 border-2 rounded-xl transition-all duration-200 text-left";
    
    if (state === 'correct') {
      return `${baseStyles} border-green-500 bg-green-50 shadow-lg`;
    } else if (state === 'incorrect') {
      return `${baseStyles} border-red-500 bg-red-50 shadow-lg`;
    } else if (isSelected) {
      return `${baseStyles} border-purple-500 bg-purple-50 shadow-md`;
    } else {
      return `${baseStyles} border-gray-300 hover:border-purple-400 hover:bg-purple-50`;
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-4">
      <Card className="shadow-xl border-0 bg-white">
        <CardHeader className="bg-gradient-to-r from-purple-600 to-blue-600 text-white">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Target className="w-5 h-5" />
              Pregunta {questionNumber} de {totalQuestions}
            </CardTitle>
            <div className="flex items-center gap-4">
              {timeRemaining !== undefined && (
                <Badge variant="secondary" className="bg-white/20 text-white">
                  <Clock className="w-4 h-4 mr-1" />
                  {Math.floor(timeRemaining / 60)}:{(timeRemaining % 60).toString().padStart(2, '0')}
                </Badge>
              )}
              <Badge variant="secondary" className="bg-white/20 text-white">
                Dificultad: {question.difficulty || 1}/10
              </Badge>
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-6">
          {/* Contenido de la pregunta */}
          <div className="mb-8">
            {renderContent(question.pregunta_texto, question.pregunta_imagen, 'question')}
          </div>

          {/* Opciones de respuesta */}
          <div className="space-y-4 mb-8">
            {Object.entries(options).map(([key, option], idx) => {
              const hasContent = (option.texto && option.texto.trim().length > 0) || (option.imagen && option.imagen.trim().length > 0);
              if (!hasContent) return null;

              const stateClasses = [
                'answer-option-game',
                ((selectedAnswer || '').toLowerCase() === key.toLowerCase()) && 'selected',
                isAnswered && key.toLowerCase() === (question.respuesta_correcta || '').toLowerCase() && 'correct',
                isAnswered && (selectedAnswer || '').toLowerCase() === key.toLowerCase() && (question.respuesta_correcta || '').toLowerCase() !== key.toLowerCase() && 'incorrect',
              ].filter(Boolean).join(' ');

              return (
                <motion.button
                  key={key}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.05 * idx }}
                  onClick={() => onAnswerSelect(key)}
                  disabled={isAnswered}
                  className={stateClasses}
                >
                  <div className="flex items-start gap-3 w-full">
                    <div className="option-label">
                      {!isAnswered && key.toUpperCase()}
                    </div>
                    <div className="option-text">
                      {renderContent(option.texto, option.imagen, `option-${key}`)}
                    </div>
                    {isAnswered && (
                      <div className="flex-shrink-0">
                        {key.toLowerCase() === (question.respuesta_correcta || '').toLowerCase() ? (
                          <CheckCircle className="w-6 h-6 text-green-500" />
                        ) : (selectedAnswer || '').toLowerCase() === key.toLowerCase() ? (
                          <XCircle className="w-6 h-6 text-red-500" />
                        ) : null}
                      </div>
                    )}
                  </div>
                </motion.button>
              );
            })}
          </div>

          {/* Explicación (si está habilitada) */}
          {showExplanation && question.explanation && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg"
            >
              <h4 className="font-semibold text-blue-800 mb-2">Explicación:</h4>
              <p className="text-blue-700">{question.explanation}</p>
            </motion.div>
          )}

          {/* Pista (si existe) */}
          {question.hint && (
            <div className="mb-6 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <h4 className="font-semibold text-yellow-800 mb-1">💡 Pista:</h4>
              <p className="text-yellow-700 text-sm">{question.hint}</p>
            </div>
          )}

          {/* Navegación */}
          <div className="flex justify-between items-center pt-4 border-t border-gray-200">
            <Button
              onClick={onPrevious}
              disabled={questionNumber <= 1}
              variant="outline"
              className="flex items-center gap-2"
            >
              <ChevronLeft className="w-4 h-4" />
              Anterior
            </Button>

            <div className="flex items-center gap-2">
              {selectedAnswer && (
                <Badge variant="secondary" className="bg-green-100 text-green-800">
                  Respuesta seleccionada: {selectedAnswer.toUpperCase()}
                </Badge>
              )}
            </div>

            <Button
              onClick={onNext}
              disabled={questionNumber >= totalQuestions}
              className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700"
            >
              Siguiente
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 