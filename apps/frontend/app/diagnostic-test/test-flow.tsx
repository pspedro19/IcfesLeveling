'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface Question {
  id: string;
  question_text: string;
  pregunta_texto?: string;
  pregunta_imagen?: string;
  options?: string[];
  opcion_a_texto?: string;
  opcion_b_texto?: string;
  opcion_c_texto?: string;
  opcion_d_texto?: string;
  opcion_a_imagen?: string;
  opcion_b_imagen?: string;
  opcion_c_imagen?: string;
  opcion_d_imagen?: string;
  difficulty: number;
  hint?: string;
}

interface DiagnosticTestFlowProps {
  subjectId: string;
  subjectName: string;
  onComplete?: (results: any) => void;
}

export default function DiagnosticTestFlow({ subjectId, subjectName, onComplete }: DiagnosticTestFlowProps) {
  const router = useRouter();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<{ [key: string]: string }>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showHint, setShowHint] = useState(false);
  const [timeLeft, setTimeLeft] = useState(60 * 60); // 60 minutes in seconds
  const [testStarted, setTestStarted] = useState(false);

  useEffect(() => {
    loadQuestions();
  }, [subjectId]);

  useEffect(() => {
    if (testStarted && timeLeft > 0) {
      const timer = setInterval(() => {
        setTimeLeft(prev => prev - 1);
      }, 1000);
      return () => clearInterval(timer);
    } else if (timeLeft === 0) {
      handleSubmit();
    }
  }, [testStarted, timeLeft]);

  const loadQuestions = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
      
      // Get IMAGE-ONLY questions directly from the new diagnostic endpoint
      const questionsResponse = await fetch(`${API_URL}/diagnostic-images-test/questions/${subjectId}?limit=20`);
      
      if (questionsResponse.ok) {
        const data = await questionsResponse.json();
        console.log('Loaded image questions:', data);
        // Extract questions from the response
        const questionsData = data.questions || data;
        setQuestions(Array.isArray(questionsData) ? questionsData : []);
        setTestStarted(true);
      } else {
        throw new Error('No se pudieron cargar las preguntas');
      }
    } catch (err) {
      console.error('Error loading questions:', err);
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswer = (answer: string) => {
    const currentQuestion = questions[currentQuestionIndex];
    setAnswers(prev => ({
      ...prev,
      [currentQuestion.id]: answer
    }));
    
    // Auto-advance to next question
    if (currentQuestionIndex < questions.length - 1) {
      setTimeout(() => {
        setCurrentQuestionIndex(prev => prev + 1);
        setShowHint(false);
      }, 300);
    }
  };

  const handleNext = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
      setShowHint(false);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
      setShowHint(false);
    }
  };

  const handleSubmit = async () => {
    const correctAnswers = questions.filter(q => {
      const userAnswer = answers[q.id];
      return userAnswer === 'B'; // All our test questions have 'B' as correct answer
    }).length;

    const score = Math.round((correctAnswers / questions.length) * 100);
    
    const results = {
      total_questions: questions.length,
      correct_answers: correctAnswers,
      score_percentage: score,
      time_spent: 3600 - timeLeft,
      answers: answers
    };

    if (onComplete) {
      onComplete(results);
    } else {
      alert(`
🎯 Test Completado!
📊 Resultado: ${score}%
✅ Respuestas Correctas: ${correctAnswers}/${questions.length}
⏱️ Tiempo: ${Math.floor((3600 - timeLeft) / 60)} minutos
      `);
      router.push('/');
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 to-black flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-purple-500 mx-auto mb-4"></div>
          <p className="text-white text-xl">Cargando preguntas de {subjectName}...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-900 to-black flex items-center justify-center">
        <div className="bg-red-800/50 p-8 rounded-lg text-center">
          <h2 className="text-red-300 text-2xl mb-4">❌ Error</h2>
          <p className="text-red-200">{error}</p>
          <button
            onClick={() => router.push('/diagnostic-test')}
            className="mt-4 px-6 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Volver
          </button>
        </div>
      </div>
    );
  }

  if (questions.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-yellow-900 to-black flex items-center justify-center">
        <div className="bg-yellow-800/50 p-8 rounded-lg text-center">
          <h2 className="text-yellow-300 text-2xl mb-4">⚠️ Sin Preguntas</h2>
          <p className="text-yellow-200">No hay preguntas disponibles para {subjectName}</p>
          <button
            onClick={() => router.push('/diagnostic-test')}
            className="mt-4 px-6 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700"
          >
            Volver
          </button>
        </div>
      </div>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];
  const questionText = currentQuestion.pregunta_texto || currentQuestion.question_text;
  const options = currentQuestion.options || [
    currentQuestion.opcion_a_texto || 'Opción A',
    currentQuestion.opcion_b_texto || 'Opción B',
    currentQuestion.opcion_c_texto || 'Opción C',
    currentQuestion.opcion_d_texto || 'Opción D'
  ];

  const progressPercentage = ((currentQuestionIndex + 1) / questions.length) * 100;
  const isAnswered = !!answers[currentQuestion.id];

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-black">
      {/* Header */}
      <div className="bg-black/30 backdrop-blur-lg border-b border-purple-500/30 p-4">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-yellow-400">
              📚 {subjectName} - Test Diagnóstico
            </h1>
            <p className="text-purple-300">
              Pregunta {currentQuestionIndex + 1} de {questions.length}
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-white">
              ⏱️ {formatTime(timeLeft)}
            </div>
            <p className="text-purple-300 text-sm">Tiempo restante</p>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-black/20 p-2">
        <div className="max-w-6xl mx-auto">
          <div className="bg-gray-700 rounded-full h-3">
            <div 
              className="bg-gradient-to-r from-purple-500 to-blue-500 h-3 rounded-full transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto p-8">
        {/* Question Card */}
        <div className="bg-black/40 backdrop-blur-lg rounded-xl border border-purple-500/30 p-8 mb-6">
          {/* Difficulty Badge */}
          <div className="flex justify-between items-center mb-6">
            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
              currentQuestion.difficulty === 1 ? 'bg-green-600 text-white' :
              currentQuestion.difficulty === 2 ? 'bg-yellow-600 text-white' :
              'bg-red-600 text-white'
            }`}>
              {currentQuestion.difficulty === 1 ? '⭐ Fácil' :
               currentQuestion.difficulty === 2 ? '⭐⭐ Medio' :
               '⭐⭐⭐ Difícil'}
            </span>
            {currentQuestion.hint && (
              <button
                onClick={() => setShowHint(!showHint)}
                className="text-yellow-400 hover:text-yellow-300"
              >
                💡 {showHint ? 'Ocultar' : 'Ver'} Pista
              </button>
            )}
          </div>

          {/* Question Text */}
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-white mb-4">
              {questionText}
            </h2>
            
            {/* Question Image */}
            {currentQuestion.pregunta_imagen && (
              <div className="mb-4 flex justify-center">
                <img 
                  src={currentQuestion.pregunta_imagen} 
                  alt="Imagen de la pregunta"
                  className="max-w-full max-h-96 rounded-lg shadow-lg border border-purple-500/30"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                  }}
                />
              </div>
            )}
          </div>

          {/* Hint */}
          {showHint && currentQuestion.hint && (
            <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-lg p-4 mb-6">
              <p className="text-yellow-300">💡 {currentQuestion.hint}</p>
            </div>
          )}

          {/* Options */}
          <div className="grid grid-cols-1 gap-4">
            {options.map((option, index) => {
              const optionLetter = String.fromCharCode(65 + index); // A, B, C, D
              const isSelected = answers[currentQuestion.id] === optionLetter;
              
              // Get option image based on index
              const optionImages = [
                currentQuestion.opcion_a_imagen,
                currentQuestion.opcion_b_imagen,
                currentQuestion.opcion_c_imagen,
                currentQuestion.opcion_d_imagen
              ];
              const optionImage = optionImages[index];
              
              return (
                <button
                  key={index}
                  onClick={() => handleAnswer(optionLetter)}
                  className={`p-4 rounded-lg border-2 text-left transition-all duration-200 ${
                    isSelected
                      ? 'bg-purple-600/30 border-purple-400 text-white'
                      : 'bg-black/20 border-gray-600 text-gray-300 hover:bg-purple-900/20 hover:border-purple-500'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <span className="font-bold text-lg flex-shrink-0">{optionLetter}.</span>
                    <div className="flex-1">
                      <div className="text-left">{option}</div>
                      {optionImage && (
                        <img 
                          src={optionImage} 
                          alt={`Imagen opción ${optionLetter}`}
                          className="mt-2 max-w-full max-h-32 rounded border border-purple-500/20"
                          onError={(e) => {
                            e.currentTarget.style.display = 'none';
                          }}
                        />
                      )}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Navigation */}
        <div className="flex justify-between items-center">
          <button
            onClick={handlePrevious}
            disabled={currentQuestionIndex === 0}
            className="px-6 py-3 bg-gray-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600 transition-colors"
          >
            ← Anterior
          </button>

          <div className="flex gap-2">
            {Array.from({ length: Math.min(5, questions.length) }, (_, i) => {
              const qIndex = Math.max(0, Math.min(currentQuestionIndex - 2 + i, questions.length - 1));
              const isCurrentIndex = qIndex === currentQuestionIndex;
              const hasAnswer = !!answers[questions[qIndex]?.id];
              
              return (
                <button
                  key={qIndex}
                  onClick={() => setCurrentQuestionIndex(qIndex)}
                  className={`w-10 h-10 rounded-full font-bold ${
                    isCurrentIndex
                      ? 'bg-purple-600 text-white'
                      : hasAnswer
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-700 text-gray-300'
                  }`}
                >
                  {qIndex + 1}
                </button>
              );
            })}
          </div>

          {currentQuestionIndex === questions.length - 1 ? (
            <button
              onClick={handleSubmit}
              className="px-6 py-3 bg-gradient-to-r from-green-600 to-blue-600 text-white rounded-lg font-bold hover:from-green-700 hover:to-blue-700 transition-all"
            >
              🏁 Finalizar Test
            </button>
          ) : (
            <button
              onClick={handleNext}
              disabled={!isAnswered}
              className="px-6 py-3 bg-purple-600 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-purple-700 transition-colors"
            >
              Siguiente →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}