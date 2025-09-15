'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Brain, 
  Lightbulb, 
  BookOpen, 
  Target, 
  Star,
  ThumbsUp,
  ThumbsDown,
  MessageSquare,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Play,
  Volume2,
  Copy,
  RefreshCw,
  Zap,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

interface AIExplanation {
  id: string;
  explanation: string;
  confidence_score: number;
  explanation_type: 'conceptual' | 'step_by_step' | 'hint' | 'error_analysis';
  difficulty_level: 'simple' | 'detailed' | 'advanced';
  key_concepts: string[];
  common_mistakes: string[];
  study_tips: string[];
  related_topics: string[];
  video_recommendations?: Array<{
    title: string;
    url: string;
    duration: string;
    thumbnail: string;
  }>;
  practice_questions?: Array<{
    id: string;
    statement: string;
    difficulty: string;
  }>;
  user_feedback?: {
    helpful: boolean;
    clarity: number;
    accuracy: number;
  };
}

interface AIExplanationPanelProps {
  explanation: AIExplanation;
  questionId: string;
  userAnswer: string;
  correctAnswer: string;
  onFeedback: (feedback: { helpful: boolean; clarity: number; accuracy: number; comments?: string }) => void;
  onRequestNewExplanation: (type: 'simpler' | 'detailed' | 'alternative') => Promise<AIExplanation>;
  onPlayAudio?: () => void;
  isAudioPlaying?: boolean;
}

export default function AIExplanationPanel({
  explanation,
  questionId,
  userAnswer,
  correctAnswer,
  onFeedback,
  onRequestNewExplanation,
  onPlayAudio,
  isAudioPlaying = false
}: AIExplanationPanelProps) {
  const [expanded, setExpanded] = useState(true);
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackData, setFeedbackData] = useState({
    helpful: true,
    clarity: 5,
    accuracy: 5,
    comments: ''
  });
  const [showRelatedContent, setShowRelatedContent] = useState(false);
  const [isRegeneratingExplanation, setIsRegeneratingExplanation] = useState(false);
  const [copiedText, setCopiedText] = useState(false);

  const isCorrectAnswer = userAnswer === correctAnswer;

  const getExplanationTypeIcon = () => {
    switch (explanation.explanation_type) {
      case 'conceptual':
        return <Brain className="h-5 w-5" />;
      case 'step_by_step':
        return <Target className="h-5 w-5" />;
      case 'hint':
        return <Lightbulb className="h-5 w-5" />;
      case 'error_analysis':
        return <AlertTriangle className="h-5 w-5" />;
      default:
        return <BookOpen className="h-5 w-5" />;
    }
  };

  const getExplanationTypeColor = () => {
    switch (explanation.explanation_type) {
      case 'conceptual':
        return 'from-blue-500 to-blue-600';
      case 'step_by_step':
        return 'from-green-500 to-green-600';
      case 'hint':
        return 'from-yellow-500 to-yellow-600';
      case 'error_analysis':
        return 'from-red-500 to-red-600';
      default:
        return 'from-purple-500 to-purple-600';
    }
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const handleCopyText = async () => {
    try {
      await navigator.clipboard.writeText(explanation.explanation);
      setCopiedText(true);
      setTimeout(() => setCopiedText(false), 2000);
    } catch (error) {
      console.error('Error copying text:', error);
    }
  };

  const handleNewExplanation = async (type: 'simpler' | 'detailed' | 'alternative') => {
    setIsRegeneratingExplanation(true);
    try {
      const newExplanation = await onRequestNewExplanation(type);
      // The parent component should handle updating the explanation
    } catch (error) {
      console.error('Error getting new explanation:', error);
    } finally {
      setIsRegeneratingExplanation(false);
    }
  };

  const submitFeedback = () => {
    onFeedback(feedbackData);
    setShowFeedback(false);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="w-full"
    >
      <Card className="overflow-hidden shadow-lg border-0 bg-gradient-to-br from-white to-gray-50">
        {/* Header */}
        <CardHeader 
          className={`bg-gradient-to-r ${getExplanationTypeColor()} text-white cursor-pointer`}
          onClick={() => setExpanded(!expanded)}
        >
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-3">
              {getExplanationTypeIcon()}
              <div>
                <span>Explicación IA</span>
                <div className="flex items-center space-x-2 mt-1">
                  <Badge variant="secondary" className="text-xs bg-white/20 text-white border-white/30">
                    {explanation.explanation_type.replace('_', ' ')}
                  </Badge>
                  <div className="flex items-center space-x-1">
                    <Sparkles className="h-3 w-3" />
                    <span className="text-xs">
                      Confianza: {(explanation.confidence_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>
            </CardTitle>
            
            <div className="flex items-center space-x-2">
              {/* Audio controls */}
              {onPlayAudio && (
                <Button
                  onClick={(e) => {
                    e.stopPropagation();
                    onPlayAudio();
                  }}
                  variant="ghost"
                  size="sm"
                  className="text-white hover:bg-white/20"
                >
                  {isAudioPlaying ? (
                    <Volume2 className="h-4 w-4 animate-pulse" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                </Button>
              )}
              
              {/* Copy button */}
              <Button
                onClick={(e) => {
                  e.stopPropagation();
                  handleCopyText();
                }}
                variant="ghost"
                size="sm"
                className="text-white hover:bg-white/20"
              >
                {copiedText ? (
                  <CheckCircle className="h-4 w-4" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
              
              {/* Expand/collapse */}
              {expanded ? (
                <ChevronUp className="h-5 w-5" />
              ) : (
                <ChevronDown className="h-5 w-5" />
              )}
            </div>
          </div>
        </CardHeader>

        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <CardContent className="p-6 space-y-6">
                {/* Answer status */}
                <div className={`p-4 rounded-xl border-2 ${
                  isCorrectAnswer 
                    ? 'bg-green-50 border-green-200' 
                    : 'bg-red-50 border-red-200'
                }`}>
                  <div className="flex items-center space-x-3">
                    {isCorrectAnswer ? (
                      <CheckCircle className="h-6 w-6 text-green-600" />
                    ) : (
                      <AlertTriangle className="h-6 w-6 text-red-600" />
                    )}
                    <div>
                      <p className={`font-semibold ${
                        isCorrectAnswer ? 'text-green-800' : 'text-red-800'
                      }`}>
                        {isCorrectAnswer ? '¡Respuesta correcta!' : 'Respuesta incorrecta'}
                      </p>
                      {!isCorrectAnswer && (
                        <p className="text-sm text-red-700">
                          Tu respuesta: <strong>{userAnswer}</strong> | 
                          Correcta: <strong>{correctAnswer}</strong>
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Main explanation */}
                <div className="prose prose-sm max-w-none">
                  <div className="bg-blue-50 p-4 rounded-xl border border-blue-200">
                    <h4 className="font-semibold text-blue-800 mb-2 flex items-center space-x-2">
                      <Brain className="h-4 w-4" />
                      <span>Explicación</span>
                    </h4>
                    <div className="text-blue-700 leading-relaxed">
                      {explanation.explanation.split('\n').map((paragraph, index) => (
                        <p key={index} className="mb-2 last:mb-0">{paragraph}</p>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Key concepts */}
                {explanation.key_concepts.length > 0 && (
                  <div>
                    <h5 className="font-semibold text-gray-800 mb-3 flex items-center space-x-2">
                      <Star className="h-4 w-4 text-yellow-500" />
                      <span>Conceptos Clave</span>
                    </h5>
                    <div className="flex flex-wrap gap-2">
                      {explanation.key_concepts.map((concept, index) => (
                        <Badge key={index} variant="secondary" className="bg-yellow-100 text-yellow-800">
                          {concept}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Common mistakes */}
                {explanation.common_mistakes.length > 0 && (
                  <div>
                    <h5 className="font-semibold text-gray-800 mb-3 flex items-center space-x-2">
                      <AlertTriangle className="h-4 w-4 text-red-500" />
                      <span>Errores Comunes</span>
                    </h5>
                    <ul className="space-y-2">
                      {explanation.common_mistakes.map((mistake, index) => (
                        <li key={index} className="flex items-start space-x-2 text-sm">
                          <div className="w-1 h-1 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
                          <span className="text-red-700">{mistake}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Study tips */}
                {explanation.study_tips.length > 0 && (
                  <div>
                    <h5 className="font-semibold text-gray-800 mb-3 flex items-center space-x-2">
                      <Lightbulb className="h-4 w-4 text-green-500" />
                      <span>Tips de Estudio</span>
                    </h5>
                    <ul className="space-y-2">
                      {explanation.study_tips.map((tip, index) => (
                        <li key={index} className="flex items-start space-x-2 text-sm">
                          <div className="w-1 h-1 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
                          <span className="text-green-700">{tip}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Video recommendations */}
                {explanation.video_recommendations && explanation.video_recommendations.length > 0 && (
                  <div>
                    <h5 className="font-semibold text-gray-800 mb-3 flex items-center space-x-2">
                      <Play className="h-4 w-4 text-purple-500" />
                      <span>Videos Recomendados</span>
                    </h5>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {explanation.video_recommendations.slice(0, 2).map((video, index) => (
                        <div key={index} className="border border-gray-200 rounded-lg p-3 hover:shadow-md transition-shadow cursor-pointer">
                          <div className="flex items-start space-x-3">
                            <div className="w-16 h-12 bg-gray-200 rounded flex items-center justify-center">
                              <Play className="h-4 w-4 text-gray-500" />
                            </div>
                            <div className="flex-1">
                              <h6 className="font-medium text-sm text-gray-800 line-clamp-2">
                                {video.title}
                              </h6>
                              <p className="text-xs text-gray-500 mt-1">{video.duration}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Action buttons */}
                <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                  <div className="flex space-x-2">
                    <Button
                      onClick={() => handleNewExplanation('simpler')}
                      disabled={isRegeneratingExplanation}
                      variant="outline"
                      size="sm"
                    >
                      {isRegeneratingExplanation ? (
                        <RefreshCw className="h-4 w-4 animate-spin mr-2" />
                      ) : (
                        <Lightbulb className="h-4 w-4 mr-2" />
                      )}
                      Más Simple
                    </Button>
                    
                    <Button
                      onClick={() => handleNewExplanation('detailed')}
                      disabled={isRegeneratingExplanation}
                      variant="outline"
                      size="sm"
                    >
                      <BookOpen className="h-4 w-4 mr-2" />
                      Más Detallado
                    </Button>
                    
                    <Button
                      onClick={() => handleNewExplanation('alternative')}
                      disabled={isRegeneratingExplanation}
                      variant="outline"
                      size="sm"
                    >
                      <Zap className="h-4 w-4 mr-2" />
                      Alternativo
                    </Button>
                  </div>

                  <Button
                    onClick={() => setShowFeedback(!showFeedback)}
                    variant="outline"
                    size="sm"
                    className="flex items-center space-x-2"
                  >
                    <MessageSquare className="h-4 w-4" />
                    <span>Feedback</span>
                  </Button>
                </div>

                {/* Feedback section */}
                <AnimatePresence>
                  {showFeedback && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="bg-gray-50 p-4 rounded-xl border border-gray-200"
                    >
                      <h5 className="font-semibold text-gray-800 mb-3">
                        ¿Qué tan útil fue esta explicación?
                      </h5>
                      
                      <div className="space-y-4">
                        <div className="flex items-center space-x-4">
                          <Button
                            onClick={() => setFeedbackData(prev => ({ ...prev, helpful: true }))}
                            variant={feedbackData.helpful ? "default" : "outline"}
                            size="sm"
                            className="flex items-center space-x-2"
                          >
                            <ThumbsUp className="h-4 w-4" />
                            <span>Útil</span>
                          </Button>
                          
                          <Button
                            onClick={() => setFeedbackData(prev => ({ ...prev, helpful: false }))}
                            variant={!feedbackData.helpful ? "default" : "outline"}
                            size="sm"
                            className="flex items-center space-x-2"
                          >
                            <ThumbsDown className="h-4 w-4" />
                            <span>No útil</span>
                          </Button>
                        </div>

                        <div className="space-y-2">
                          <div>
                            <label className="text-sm font-medium text-gray-700">
                              Claridad (1-5): {feedbackData.clarity}
                            </label>
                            <Progress value={feedbackData.clarity * 20} className="h-2 mt-1" />
                            <input
                              type="range"
                              min="1"
                              max="5"
                              value={feedbackData.clarity}
                              onChange={(e) => setFeedbackData(prev => ({ ...prev, clarity: parseInt(e.target.value) }))}
                              className="w-full mt-1"
                            />
                          </div>

                          <div>
                            <label className="text-sm font-medium text-gray-700">
                              Precisión (1-5): {feedbackData.accuracy}
                            </label>
                            <Progress value={feedbackData.accuracy * 20} className="h-2 mt-1" />
                            <input
                              type="range"
                              min="1"
                              max="5"
                              value={feedbackData.accuracy}
                              onChange={(e) => setFeedbackData(prev => ({ ...prev, accuracy: parseInt(e.target.value) }))}
                              className="w-full mt-1"
                            />
                          </div>
                        </div>

                        <textarea
                          placeholder="Comentarios adicionales (opcional)"
                          value={feedbackData.comments}
                          onChange={(e) => setFeedbackData(prev => ({ ...prev, comments: e.target.value }))}
                          className="w-full p-2 border border-gray-300 rounded-lg text-sm"
                          rows={3}
                        />

                        <div className="flex justify-end space-x-2">
                          <Button
                            onClick={() => setShowFeedback(false)}
                            variant="outline"
                            size="sm"
                          >
                            Cancelar
                          </Button>
                          <Button
                            onClick={submitFeedback}
                            size="sm"
                          >
                            Enviar Feedback
                          </Button>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </CardContent>
            </motion.div>
          )}
        </AnimatePresence>
      </Card>
    </motion.div>
  );
}