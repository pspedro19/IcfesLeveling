'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Brain,
  CheckCircle,
  XCircle,
  Lightbulb,
  BookOpen,
  Loader2,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { aiTipsService } from '@/services/ai-tips.service';

interface AIExplanationProps {
  questionId: string;
  userAnswer: string;
  isCorrect: boolean;
  correctAnswer?: string;
  hint?: string;
  onClose?: () => void;
}

export default function AIExplanation({
  questionId,
  userAnswer,
  isCorrect,
  correctAnswer,
  hint,
  onClose
}: AIExplanationProps) {
  const [explanation, setExplanation] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isGenerated, setIsGenerated] = useState(false);
  const [showFullExplanation, setShowFullExplanation] = useState(false);
  
  useEffect(() => {
    const fetchExplanation = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await aiTipsService.getQuestionExplanation(
          questionId,
          userAnswer,
          isCorrect
        );
        
        setExplanation(response.explanation);
        setIsGenerated(response.generated);
        if (!correctAnswer && response.correctAnswer) {
          // Use correct answer from response if not provided
        }
      } catch (err) {
        setError('Error al cargar explicación');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchExplanation();
  }, [questionId, userAnswer, isCorrect]);
  
  const getIcon = () => {
    if (isCorrect) {
      return <CheckCircle className="w-8 h-8 text-green-400" />;
    } else {
      return <XCircle className="w-8 h-8 text-red-400" />;
    }
  };
  
  return (
    <motion.div
      className={`rounded-lg overflow-hidden border ${
        isCorrect 
          ? 'bg-green-900/20 border-green-500/30' 
          : 'bg-red-900/20 border-red-500/30'
      }`}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
    >
      {/* Header */}
      <div className={`px-4 py-3 ${
        isCorrect ? 'bg-green-900/30' : 'bg-red-900/30'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {getIcon()}
            <div>
              <h3 className="font-semibold text-white">
                {isCorrect ? '¡Respuesta Correcta!' : 'Respuesta Incorrecta'}
              </h3>
              <p className="text-sm text-gray-400">
                Tu respuesta: <span className="text-white">{userAnswer}</span>
              </p>
            </div>
          </div>
          
          {isGenerated && (
            <div className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-purple-400" />
              <span className="text-xs text-purple-400">IA</span>
            </div>
          )}
        </div>
      </div>
      
      {/* Content */}
      <div className="p-4">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 text-purple-400 animate-spin" />
          </div>
        ) : error ? (
          <div className="text-red-400 text-center py-4">
            {error}
          </div>
        ) : (
          <div className="space-y-4">
            {/* Correct Answer Display */}
            {!isCorrect && correctAnswer && (
              <div className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50">
                <div className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-green-400 mt-0.5" />
                  <div>
                    <p className="text-sm text-gray-400">Respuesta correcta:</p>
                    <p className="text-white font-semibold">{correctAnswer}</p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Explanation */}
            <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
              <div className="flex items-start gap-3">
                <BookOpen className="w-5 h-5 text-purple-400 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-semibold text-white mb-2">Explicación</h4>
                  <p className={`text-sm text-gray-300 leading-relaxed ${
                    !showFullExplanation && explanation.length > 200 ? 'line-clamp-3' : ''
                  }`}>
                    {explanation}
                  </p>
                  
                  {explanation.length > 200 && (
                    <button
                      onClick={() => setShowFullExplanation(!showFullExplanation)}
                      className="mt-2 text-purple-400 hover:text-purple-300 text-sm 
                        flex items-center gap-1 transition-colors"
                    >
                      {showFullExplanation ? (
                        <>
                          <span>Ver menos</span>
                          <ChevronUp className="w-4 h-4" />
                        </>
                      ) : (
                        <>
                          <span>Ver más</span>
                          <ChevronDown className="w-4 h-4" />
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            </div>
            
            {/* Hint */}
            {hint && (
              <div className="bg-yellow-900/20 rounded-lg p-3 border border-yellow-500/30">
                <div className="flex items-start gap-3">
                  <Lightbulb className="w-5 h-5 text-yellow-400 mt-0.5" />
                  <div>
                    <p className="text-sm font-semibold text-yellow-400 mb-1">
                      Pista para la próxima vez:
                    </p>
                    <p className="text-sm text-gray-300">{hint}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* Action Button */}
        {onClose && (
          <motion.button
            onClick={onClose}
            className={`w-full mt-4 py-3 rounded-lg font-semibold transition-all ${
              isCorrect
                ? 'bg-green-600 hover:bg-green-700 text-white'
                : 'bg-red-600 hover:bg-red-700 text-white'
            }`}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            Continuar
          </motion.button>
        )}
      </div>
    </motion.div>
  );
}