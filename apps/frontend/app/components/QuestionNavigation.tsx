'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Grid3X3, 
  CheckCircle, 
  Circle, 
  Target,
  Clock,
  BarChart3
} from 'lucide-react';

interface QuestionNavigationProps {
  totalQuestions: number;
  currentQuestion: number;
  answeredQuestions: number[];
  onQuestionSelect: (questionNumber: number) => void;
  timeRemaining?: number;
  progress?: number;
  className?: string;
}

export default function QuestionNavigation({
  totalQuestions,
  currentQuestion,
  answeredQuestions,
  onQuestionSelect,
  timeRemaining,
  progress,
  className = ""
}: QuestionNavigationProps) {
  // Calcular dimensiones de la cuadrícula (9x5 para 45 preguntas)
  const gridCols = 9;
  const gridRows = Math.ceil(totalQuestions / gridCols);

  const getQuestionState = (questionNumber: number) => {
    if (questionNumber === currentQuestion) return 'current';
    if (answeredQuestions.includes(questionNumber)) return 'answered';
    return 'unanswered';
  };

  const getQuestionStyles = (questionNumber: number) => {
    const state = getQuestionState(questionNumber);
    const isCurrent = questionNumber === currentQuestion;
    
    const baseStyles = "w-10 h-10 rounded-lg border-2 font-bold text-sm transition-all duration-200 flex items-center justify-center cursor-pointer hover:scale-110";
    
    switch (state) {
      case 'current':
        return `${baseStyles} bg-purple-600 text-white border-purple-700 shadow-lg shadow-purple-500/50`;
      case 'answered':
        return `${baseStyles} bg-green-500 text-white border-green-600 shadow-md`;
      case 'unanswered':
        return `${baseStyles} bg-gray-100 text-gray-600 border-gray-300 hover:bg-gray-200`;
      default:
        return baseStyles;
    }
  };

  const getQuestionIcon = (questionNumber: number) => {
    const state = getQuestionState(questionNumber);
    
    switch (state) {
      case 'current':
        return <Target className="w-4 h-4" />;
      case 'answered':
        return <CheckCircle className="w-4 h-4" />;
      case 'unanswered':
        return <Circle className="w-4 h-4" />;
      default:
        return questionNumber;
    }
  };

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <Card className={`bg-white shadow-lg border-0 ${className}`}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-lg">
          <div className="flex items-center gap-2">
            <Grid3X3 className="w-5 h-5 text-purple-600" />
            Navegación de Preguntas
          </div>
          <div className="flex items-center gap-2">
            {timeRemaining !== undefined && (
              <Badge variant="secondary" className="bg-red-100 text-red-800">
                <Clock className="w-3 h-3 mr-1" />
                {formatTime(timeRemaining)}
              </Badge>
            )}
            {progress !== undefined && (
              <Badge variant="secondary" className="bg-blue-100 text-blue-800">
                <BarChart3 className="w-3 h-3 mr-1" />
                {Math.round(progress)}%
              </Badge>
            )}
          </div>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="pt-0">
        {/* Cuadrícula de preguntas */}
        <div className="mb-4">
          <div 
            className="grid gap-2"
            style={{
              gridTemplateColumns: `repeat(${gridCols}, 1fr)`,
              gridTemplateRows: `repeat(${gridRows}, 1fr)`
            }}
          >
            {Array.from({ length: totalQuestions }, (_, index) => {
              const questionNumber = index + 1;
              const state = getQuestionState(questionNumber);
              
              return (
                <motion.button
                  key={questionNumber}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.01 }}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => onQuestionSelect(questionNumber)}
                  className={getQuestionStyles(questionNumber)}
                  title={`Pregunta ${questionNumber} - ${state === 'current' ? 'Actual' : state === 'answered' ? 'Respondida' : 'Sin responder'}`}
                >
                  {getQuestionIcon(questionNumber)}
                </motion.button>
              );
            })}
          </div>
        </div>

        {/* Leyenda */}
        <div className="flex items-center justify-between text-sm text-gray-600">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-purple-600 rounded border border-purple-700"></div>
              <span>Actual</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-green-500 rounded border border-green-600"></div>
              <span>Respondida</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-gray-100 rounded border border-gray-300"></div>
              <span>Sin responder</span>
            </div>
          </div>
          
          <div className="text-right">
            <div className="font-semibold">
              {answeredQuestions.length} / {totalQuestions} respondidas
            </div>
            <div className="text-xs text-gray-500">
              {Math.round((answeredQuestions.length / totalQuestions) * 100)}% completado
            </div>
          </div>
        </div>

        {/* Barra de progreso */}
        <div className="mt-3">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <motion.div
              className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${(answeredQuestions.length / totalQuestions) * 100}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
} 