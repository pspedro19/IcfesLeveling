'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Clock, 
  Target, 
  Lightbulb, 
  CheckCircle, 
  XCircle, 
  Star,
  Flame,
  Zap,
  Heart,
  Shield
} from 'lucide-react';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";

interface Question {
  id: string;
  statement: string;
  options: {
    A: string;
    B: string;
    C: string;
    D: string;
  };
  correct_answer: string;
  topic?: string;
  difficulty?: 'easy' | 'medium' | 'hard';
  estimated_time?: string;
  explanation?: string;
  hints?: string[];
}

interface InteractiveQuestionCardProps {
  question: Question;
  onAnswer: (answer: string, timeSpent: number, hintsUsed: number) => void;
  onRequestHint: () => Promise<string>;
  showResult?: boolean;
  userAnswer?: string;
  streakCount?: number;
  comboMultiplier?: number;
  healthPoints?: number;
  maxHealth?: number;
}

const difficultyColors = {
  easy: 'from-green-400 to-green-600',
  medium: 'from-yellow-400 to-orange-500',
  hard: 'from-red-400 to-red-600'
};

const difficultyIcons = {
  easy: Shield,
  medium: Target,
  hard: Flame
};

export default function InteractiveQuestionCard({
  question,
  onAnswer,
  onRequestHint,
  showResult = false,
  userAnswer,
  streakCount = 0,
  comboMultiplier = 1,
  healthPoints = 100,
  maxHealth = 100
}: InteractiveQuestionCardProps) {
  const [selectedAnswer, setSelectedAnswer] = useState<string>('');
  const [timeSpent, setTimeSpent] = useState(0);
  const [isAnswered, setIsAnswered] = useState(false);
  const [hintsUsed, setHintsUsed] = useState(0);
  const [currentHints, setCurrentHints] = useState<string[]>([]);
  const [showHints, setShowHints] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [animateCorrect, setAnimateCorrect] = useState(false);
  const [animateIncorrect, setAnimateIncorrect] = useState(false);

  // Timer effect
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (!isAnswered && !showResult) {
      interval = setInterval(() => {
        setTimeSpent(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isAnswered, showResult]);

  // Result animation effect
  useEffect(() => {
    if (showResult && userAnswer) {
      const isCorrect = userAnswer === question.correct_answer;
      if (isCorrect) {
        setAnimateCorrect(true);
        setTimeout(() => setAnimateCorrect(false), 2000);
      } else {
        setAnimateIncorrect(true);
        setTimeout(() => setAnimateIncorrect(false), 2000);
      }
    }
  }, [showResult, userAnswer, question.correct_answer]);

  const handleAnswerSubmit = () => {
    if (!selectedAnswer) return;
    
    setIsAnswered(true);
    onAnswer(selectedAnswer, timeSpent, hintsUsed);
  };

  const handleGetHint = async () => {
    if (hintsUsed >= 3) return; // Max 3 hints per question
    
    setIsLoading(true);
    try {
      const hint = await onRequestHint();
      setCurrentHints(prev => [...prev, hint]);
      setHintsUsed(prev => prev + 1);
      setShowHints(true);
    } catch (error) {
      console.error('Error getting hint:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const DifficultyIcon = question.difficulty ? difficultyIcons[question.difficulty] : Target;
  const isCorrect = showResult && userAnswer === question.correct_answer;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="w-full max-w-4xl mx-auto"
    >
      <Card className={`relative overflow-hidden shadow-xl transition-all duration-300 ${
        animateCorrect ? 'ring-4 ring-green-400 bg-green-50' : 
        animateIncorrect ? 'ring-4 ring-red-400 bg-red-50' : ''
      }`}>
        {/* Particle effects for correct answers */}
        <AnimatePresence>
          {animateCorrect && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 pointer-events-none z-50"
            >
              {[...Array(10)].map((_, i) => (
                <motion.div
                  key={i}
                  initial={{ 
                    opacity: 1, 
                    scale: 0, 
                    x: Math.random() * 300,
                    y: Math.random() * 200
                  }}
                  animate={{ 
                    opacity: 0, 
                    scale: 1,
                    x: Math.random() * 400,
                    y: Math.random() * 300
                  }}
                  transition={{ duration: 2 }}
                  className="absolute w-2 h-2 bg-yellow-400 rounded-full"
                />
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Header with game stats */}
        <div className="bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 p-4 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {/* Streak indicator */}
              <div className="flex items-center space-x-1">
                <Flame className="h-5 w-5 text-orange-300" />
                <span className="font-bold text-lg">{streakCount}</span>
                <span className="text-sm opacity-80">racha</span>
              </div>

              {/* Combo multiplier */}
              {comboMultiplier > 1 && (
                <div className="flex items-center space-x-1 bg-yellow-500/20 px-2 py-1 rounded-full">
                  <Zap className="h-4 w-4 text-yellow-300" />
                  <span className="font-bold">{comboMultiplier}x</span>
                </div>
              )}

              {/* Question metadata */}
              <div className="flex items-center space-x-2">
                {question.difficulty && (
                  <div className={`p-1 rounded-full bg-gradient-to-r ${difficultyColors[question.difficulty]}`}>
                    <DifficultyIcon className="h-4 w-4 text-white" />
                  </div>
                )}
                {question.estimated_time && (
                  <span className="text-sm opacity-80">{question.estimated_time}</span>
                )}
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {/* Health points */}
              <div className="flex items-center space-x-2">
                <Heart className={`h-5 w-5 ${healthPoints > 50 ? 'text-red-300' : 'text-gray-400'}`} />
                <div className="w-20 bg-white/20 rounded-full h-2">
                  <div 
                    className="bg-red-400 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${(healthPoints / maxHealth) * 100}%` }}
                  />
                </div>
                <span className="text-sm font-medium">{healthPoints}</span>
              </div>

              {/* Timer */}
              <div className="flex items-center space-x-2">
                <Clock className="h-5 w-5" />
                <span className="font-mono text-lg">{formatTime(timeSpent)}</span>
              </div>
            </div>
          </div>
        </div>

        <CardContent className="p-6 space-y-6">
          {/* Topic tag */}
          {question.topic && (
            <div className="flex items-center space-x-2">
              <div className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                {question.topic}
              </div>
            </div>
          )}

          {/* Question statement */}
          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-gray-900 leading-relaxed">
              {question.statement}
            </h3>
          </div>

          {/* Answer options */}
          <div className="grid gap-3">
            {Object.entries(question.options).map(([option, text]) => {
              const isSelected = selectedAnswer === option;
              const isCorrectAnswer = showResult && option === question.correct_answer;
              const isUserWrong = showResult && userAnswer === option && !isCorrectAnswer;
              
              return (
                <motion.button
                  key={option}
                  whileHover={{ scale: isAnswered ? 1 : 1.02 }}
                  whileTap={{ scale: isAnswered ? 1 : 0.98 }}
                  onClick={() => !isAnswered && !showResult && setSelectedAnswer(option)}
                  disabled={isAnswered || showResult}
                  className={`
                    w-full text-left p-4 rounded-xl border-2 transition-all duration-300 relative overflow-hidden
                    ${isSelected && !showResult ? 'border-blue-500 bg-blue-50 shadow-md' : 
                      isCorrectAnswer ? 'border-green-500 bg-green-50 shadow-md' :
                      isUserWrong ? 'border-red-500 bg-red-50 shadow-md' :
                      'border-gray-200 hover:border-gray-300 hover:bg-gray-50'}
                    ${isAnswered || showResult ? 'cursor-not-allowed opacity-90' : 'cursor-pointer'}
                  `}
                >
                  {/* Background animation for correct answer */}
                  {isCorrectAnswer && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0 }}
                      animate={{ opacity: 0.1, scale: 1 }}
                      className="absolute inset-0 bg-green-400"
                    />
                  )}
                  
                  <div className="flex items-start space-x-4 relative z-10">
                    <div className={`
                      flex-shrink-0 w-8 h-8 rounded-full border-2 flex items-center justify-center font-bold
                      ${isSelected && !showResult ? 'border-blue-500 bg-blue-500 text-white' :
                        isCorrectAnswer ? 'border-green-500 bg-green-500 text-white' :
                        isUserWrong ? 'border-red-500 bg-red-500 text-white' :
                        'border-gray-300 text-gray-600'}
                    `}>
                      {option}
                    </div>
                    <span className="text-gray-900 flex-1">{text}</span>
                    
                    {/* Status icons */}
                    {showResult && (
                      <div className="flex-shrink-0">
                        {isCorrectAnswer ? (
                          <CheckCircle className="h-5 w-5 text-green-500" />
                        ) : isUserWrong ? (
                          <XCircle className="h-5 w-5 text-red-500" />
                        ) : null}
                      </div>
                    )}
                  </div>
                </motion.button>
              );
            })}
          </div>

          {/* Hints section */}
          <AnimatePresence>
            {showHints && currentHints.length > 0 && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="bg-yellow-50 border border-yellow-200 rounded-xl p-4"
              >
                <div className="flex items-center space-x-2 mb-3">
                  <Lightbulb className="h-5 w-5 text-yellow-600" />
                  <span className="font-medium text-yellow-800">
                    Pistas ({hintsUsed}/3)
                  </span>
                </div>
                <div className="space-y-2">
                  {currentHints.map((hint, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.2 }}
                      className="text-sm text-yellow-700 bg-yellow-100 p-3 rounded-lg"
                    >
                      <span className="font-medium">Pista {index + 1}:</span> {hint}
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Action buttons */}
          {!showResult && (
            <div className="flex items-center justify-between pt-4">
              <div className="flex space-x-3">
                <Button
                  onClick={handleGetHint}
                  disabled={hintsUsed >= 3 || isLoading}
                  variant="outline"
                  size="sm"
                  className="flex items-center space-x-2"
                >
                  <Lightbulb className="h-4 w-4" />
                  <span>
                    {isLoading ? 'Generando...' : `Pista ${hintsUsed > 0 ? `(${hintsUsed}/3)` : ''}`}
                  </span>
                </Button>
              </div>

              <Button
                onClick={handleAnswerSubmit}
                disabled={!selectedAnswer || isAnswered}
                className="flex items-center space-x-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
              >
                <span>Responder</span>
                <Target className="h-4 w-4" />
              </Button>
            </div>
          )}

          {/* Result display */}
          {showResult && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className={`p-4 rounded-xl border-2 ${
                isCorrect 
                  ? 'bg-green-50 border-green-200' 
                  : 'bg-red-50 border-red-200'
              }`}
            >
              <div className="flex items-center space-x-3 mb-3">
                {isCorrect ? (
                  <CheckCircle className="h-6 w-6 text-green-600" />
                ) : (
                  <XCircle className="h-6 w-6 text-red-600" />
                )}
                <div>
                  <h4 className={`font-semibold ${
                    isCorrect ? 'text-green-800' : 'text-red-800'
                  }`}>
                    {isCorrect ? '¡Respuesta correcta!' : 'Respuesta incorrecta'}
                  </h4>
                  {!isCorrect && (
                    <p className="text-sm text-red-700">
                      La respuesta correcta es: <strong>{question.correct_answer}</strong>
                    </p>
                  )}
                </div>
              </div>

              {/* Points earned */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-1">
                    <Star className="h-4 w-4 text-yellow-500" />
                    <span className="text-sm font-medium">
                      {isCorrect ? `+${Math.round(100 * comboMultiplier)}` : '+0'} puntos
                    </span>
                  </div>
                  <div className="text-sm text-gray-600">
                    Tiempo: {formatTime(timeSpent)}
                  </div>
                  {hintsUsed > 0 && (
                    <div className="text-sm text-gray-600">
                      Pistas: {hintsUsed}/3
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}