'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  CheckCircle, 
  AlertTriangle,
  Clock,
  Target,
  BarChart3
} from 'lucide-react';

import MultimediaQuestion from '../components/MultimediaQuestion';
import QuestionNavigation from '../components/QuestionNavigation';

// Tipos
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

interface ExamState {
  questions: MultimediaQuestion[];
  currentQuestionIndex: number;
  answers: Record<string, string>;
  timeRemaining: number;
  examStarted: boolean;
  examCompleted: boolean;
  showResults: boolean;
}

export default function MultimediaExamPage() {
  // Estado del examen
  const [examState, setExamState] = useState<ExamState>({
    questions: [],
    currentQuestionIndex: 0,
    answers: {},
    timeRemaining: 3600, // 1 hora
    examStarted: false,
    examCompleted: false,
    showResults: false
  });

  const [isLoading, setIsLoading] = useState(false);
  const [timerActive, setTimerActive] = useState(false);

  // Datos de ejemplo para demostración
  const mockQuestions: MultimediaQuestion[] = [
    {
      id: '1',
      pregunta_texto: '¿Cuál es la capital de Francia?',
      opcion_a_texto: 'Londres',
      opcion_b_texto: 'París',
      opcion_c_texto: 'Madrid',
      opcion_d_texto: 'Roma',
      respuesta_correcta: 'b',
      difficulty: 1
    },
    {
      id: '2',
      pregunta_texto: '¿Qué representa la siguiente imagen?',
      pregunta_imagen: 'https://via.placeholder.com/400x300/4F46E5/FFFFFF?text=Imagen+de+Ejemplo',
      opcion_a_texto: 'Un triángulo',
      opcion_b_texto: 'Un círculo',
      opcion_c_texto: 'Un cuadrado',
      opcion_d_texto: 'Un rectángulo',
      respuesta_correcta: 'c',
      difficulty: 2
    },
    {
      id: '3',
      pregunta_texto: 'Selecciona la opción correcta basándote en la imagen:',
      opcion_a_texto: 'Opción A',
      opcion_a_imagen: 'https://via.placeholder.com/200x150/10B981/FFFFFF?text=Opción+A',
      opcion_b_texto: 'Opción B',
      opcion_b_imagen: 'https://via.placeholder.com/200x150/F59E0B/FFFFFF?text=Opción+B',
      opcion_c_texto: 'Opción C',
      opcion_c_imagen: 'https://via.placeholder.com/200x150/EF4444/FFFFFF?text=Opción+C',
      opcion_d_texto: 'Opción D',
      opcion_d_imagen: 'https://via.placeholder.com/200x150/8B5CF6/FFFFFF?text=Opción+D',
      respuesta_correcta: 'a',
      difficulty: 3,
      hint: 'Observa cuidadosamente los colores en las imágenes'
    }
  ];

  // Generar 45 preguntas de ejemplo
  const generateMockQuestions = (): MultimediaQuestion[] => {
    const questions: MultimediaQuestion[] = [];
    
    for (let i = 1; i <= 45; i++) {
      const questionType = i % 3; // 0: solo texto, 1: texto + imagen, 2: opciones con imágenes
      
      let question: MultimediaQuestion = {
        id: i.toString(),
        respuesta_correcta: ['a', 'b', 'c', 'd'][Math.floor(Math.random() * 4)],
        difficulty: Math.floor(Math.random() * 5) + 1
      };

      switch (questionType) {
        case 0:
          question.pregunta_texto = `Pregunta ${i}: ¿Cuál es la respuesta correcta para esta pregunta de ejemplo?`;
          question.opcion_a_texto = `Opción A para pregunta ${i}`;
          question.opcion_b_texto = `Opción B para pregunta ${i}`;
          question.opcion_c_texto = `Opción C para pregunta ${i}`;
          question.opcion_d_texto = `Opción D para pregunta ${i}`;
          break;
        case 1:
          question.pregunta_texto = `Pregunta ${i}: Observa la imagen y responde:`;
          question.pregunta_imagen = `https://via.placeholder.com/400x300/${Math.floor(Math.random()*16777215).toString(16)}/FFFFFF?text=Imagen+${i}`;
          question.opcion_a_texto = `Opción A para pregunta ${i}`;
          question.opcion_b_texto = `Opción B para pregunta ${i}`;
          question.opcion_c_texto = `Opción C para pregunta ${i}`;
          question.opcion_d_texto = `Opción D para pregunta ${i}`;
          break;
        case 2:
          question.pregunta_texto = `Pregunta ${i}: Selecciona la opción correcta:`;
          question.opcion_a_texto = `Opción A`;
          question.opcion_a_imagen = `https://via.placeholder.com/150x100/10B981/FFFFFF?text=A`;
          question.opcion_b_texto = `Opción B`;
          question.opcion_b_imagen = `https://via.placeholder.com/150x100/F59E0B/FFFFFF?text=B`;
          question.opcion_c_texto = `Opción C`;
          question.opcion_c_imagen = `https://via.placeholder.com/150x100/EF4444/FFFFFF?text=C`;
          question.opcion_d_texto = `Opción D`;
          question.opcion_d_imagen = `https://via.placeholder.com/150x100/8B5CF6/FFFFFF?text=D`;
          break;
      }

      questions.push(question);
    }
    
    return questions;
  };

  // Inicializar examen
  const startExam = useCallback(() => {
    setIsLoading(true);
    
    // Simular carga de preguntas
    setTimeout(() => {
      setExamState(prev => ({
        ...prev,
        questions: generateMockQuestions(),
        examStarted: true,
        timeRemaining: 3600
      }));
      setTimerActive(true);
      setIsLoading(false);
    }, 1500);
  }, []);

  // Manejar selección de respuesta
  const handleAnswerSelect = (answer: string) => {
    const currentQuestion = examState.questions[examState.currentQuestionIndex];
    if (!currentQuestion) return;

    setExamState(prev => ({
      ...prev,
      answers: {
        ...prev.answers,
        [currentQuestion.id]: answer
      }
    }));
  };

  // Navegación entre preguntas
  const goToQuestion = (questionNumber: number) => {
    const questionIndex = questionNumber - 1;
    if (questionIndex >= 0 && questionIndex < examState.questions.length) {
      setExamState(prev => ({
        ...prev,
        currentQuestionIndex: questionIndex
      }));
    }
  };

  const goToNext = () => {
    if (examState.currentQuestionIndex < examState.questions.length - 1) {
      setExamState(prev => ({
        ...prev,
        currentQuestionIndex: prev.currentQuestionIndex + 1
      }));
    }
  };

  const goToPrevious = () => {
    if (examState.currentQuestionIndex > 0) {
      setExamState(prev => ({
        ...prev,
        currentQuestionIndex: prev.currentQuestionIndex - 1
      }));
    }
  };

  // Finalizar examen
  const finishExam = () => {
    setTimerActive(false);
    setExamState(prev => ({
      ...prev,
      examCompleted: true,
      showResults: true
    }));
  };

  // Timer
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (timerActive && examState.timeRemaining > 0) {
      interval = setInterval(() => {
        setExamState(prev => {
          const newTime = prev.timeRemaining - 1;
          
          if (newTime <= 0) {
            setTimerActive(false);
            return {
              ...prev,
              timeRemaining: 0,
              examCompleted: true,
              showResults: true
            };
          }
          
          return {
            ...prev,
            timeRemaining: newTime
          };
        });
      }, 1000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [timerActive, examState.timeRemaining]);

  // Calcular estadísticas
  const calculateStats = () => {
    const totalQuestions = examState.questions.length;
    const answeredQuestions = Object.keys(examState.answers).length;
    const correctAnswers = examState.questions.reduce((count, question) => {
      const userAnswer = examState.answers[question.id];
      return count + (userAnswer === question.respuesta_correcta ? 1 : 0);
    }, 0);
    
    return {
      total: totalQuestions,
      answered: answeredQuestions,
      correct: correctAnswers,
      percentage: totalQuestions > 0 ? Math.round((correctAnswers / totalQuestions) * 100) : 0
    };
  };

  // Renderizar resultados
  if (examState.showResults) {
    const stats = calculateStats();
    
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 p-4">
        <div className="max-w-4xl mx-auto">
          <Card className="shadow-xl border-0 bg-white">
            <CardHeader className="text-center bg-gradient-to-r from-green-600 to-blue-600 text-white">
              <CardTitle className="text-3xl">🏆 Examen Completado</CardTitle>
            </CardHeader>
            <CardContent className="p-8">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="text-center">
                  <div className="text-4xl font-bold text-purple-600">{stats.correct}</div>
                  <div className="text-gray-600">Respuestas Correctas</div>
                </div>
                <div className="text-center">
                  <div className="text-4xl font-bold text-blue-600">{stats.answered}</div>
                  <div className="text-gray-600">Preguntas Respondidas</div>
                </div>
                <div className="text-center">
                  <div className="text-4xl font-bold text-green-600">{stats.percentage}%</div>
                  <div className="text-gray-600">Puntuación</div>
                </div>
              </div>
              
              <div className="text-center">
                <Button 
                  onClick={() => window.location.reload()}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Reiniciar Examen
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Renderizar pantalla de inicio
  if (!examState.examStarted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 p-4">
        <div className="max-w-2xl mx-auto">
          <Card className="shadow-xl border-0 bg-white">
            <CardHeader className="text-center bg-gradient-to-r from-purple-600 to-blue-600 text-white">
              <CardTitle className="text-3xl">📝 Examen Multimedia</CardTitle>
            </CardHeader>
            <CardContent className="p-8">
              <div className="text-center mb-8">
                <h2 className="text-2xl font-semibold mb-4">Sistema de Preguntas Multimedia</h2>
                <p className="text-gray-600 mb-6">
                  Este examen incluye 45 preguntas con soporte para texto e imágenes.
                  Tienes 60 minutos para completarlo.
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  <div className="p-4 bg-purple-50 rounded-lg">
                    <h3 className="font-semibold text-purple-800 mb-2">Características</h3>
                    <ul className="text-sm text-purple-700 space-y-1">
                      <li>• Preguntas con texto e imágenes</li>
                      <li>• Opciones multimedia</li>
                      <li>• Navegación por cuadrícula</li>
                      <li>• Temporizador integrado</li>
                    </ul>
                  </div>
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <h3 className="font-semibold text-blue-800 mb-2">Instrucciones</h3>
                    <ul className="text-sm text-blue-700 space-y-1">
                      <li>• Lee cuidadosamente cada pregunta</li>
                      <li>• Selecciona la respuesta correcta</li>
                      <li>• Usa la navegación para revisar</li>
                      <li>• Completa todas las preguntas</li>
                    </ul>
                  </div>
                </div>
              </div>
              
              <div className="text-center">
                <Button 
                  onClick={startExam}
                  disabled={isLoading}
                  className="bg-purple-600 hover:bg-purple-700 text-lg px-8 py-3"
                >
                  {isLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                      Cargando...
                    </>
                  ) : (
                    <>
                      <Play className="w-5 h-5 mr-2" />
                      Iniciar Examen
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Renderizar examen
  const currentQuestion = examState.questions[examState.currentQuestionIndex];
  const answeredQuestions = Object.keys(examState.answers).map(id => 
    examState.questions.findIndex(q => q.id === id) + 1
  );
  const progress = (answeredQuestions.length / examState.questions.length) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50">
      <div className="flex h-screen">
        {/* Panel de navegación (lado izquierdo) */}
        <div className="w-80 bg-white shadow-lg overflow-y-auto">
          <QuestionNavigation
            totalQuestions={examState.questions.length}
            currentQuestion={examState.currentQuestionIndex + 1}
            answeredQuestions={answeredQuestions}
            onQuestionSelect={goToQuestion}
            timeRemaining={examState.timeRemaining}
            progress={progress}
            className="h-full"
          />
        </div>

        {/* Contenido principal */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-4">
            {/* Header del examen */}
            <div className="mb-4">
              <Card className="bg-white shadow-md">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <Badge variant="secondary" className="bg-purple-100 text-purple-800">
                        <Target className="w-4 h-4 mr-1" />
                        Pregunta {examState.currentQuestionIndex + 1} de {examState.questions.length}
                      </Badge>
                      <Badge variant="secondary" className="bg-red-100 text-red-800">
                        <Clock className="w-4 h-4 mr-1" />
                        {Math.floor(examState.timeRemaining / 60)}:{(examState.timeRemaining % 60).toString().padStart(2, '0')}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        onClick={finishExam}
                        variant="outline"
                        className="border-red-300 text-red-600 hover:bg-red-50"
                      >
                        Finalizar Examen
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Pregunta actual */}
            {currentQuestion && (
              <MultimediaQuestion
                question={currentQuestion}
                questionNumber={examState.currentQuestionIndex + 1}
                totalQuestions={examState.questions.length}
                selectedAnswer={examState.answers[currentQuestion.id]}
                onAnswerSelect={handleAnswerSelect}
                onNext={goToNext}
                onPrevious={goToPrevious}
                timeRemaining={examState.timeRemaining}
                isAnswered={!!examState.answers[currentQuestion.id]}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 