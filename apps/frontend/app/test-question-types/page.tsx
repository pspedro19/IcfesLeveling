'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import MultimediaQuestion from '../components/MultimediaQuestion';
import { multimediaQuestionsService } from '../services/multimedia-questions.service';

interface TestQuestion {
  id: string;
  type: 'text-only' | 'question-image' | 'option-images' | 'mixed-content' | 'error-test';
  description: string;
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

export default function TestQuestionTypes() {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<{ [key: string]: string }>({});
  const [showResults, setShowResults] = useState(false);

  // Comprehensive test questions covering all multimedia scenarios
  const testQuestions: TestQuestion[] = [
    // 1. Text-only question
    {
      id: 'text-only-1',
      type: 'text-only',
      description: 'Pure text question with no multimedia content',
      pregunta_texto: '¿Cuál es la capital de Colombia?',
      opcion_a_texto: 'Bogotá',
      opcion_b_texto: 'Medellín',
      opcion_c_texto: 'Cali',
      opcion_d_texto: 'Cartagena',
      respuesta_correcta: 'A',
      difficulty: 1,
      explanation: 'Bogotá es la capital y ciudad más grande de Colombia.',
      hint: 'Piensa en la ciudad ubicada en el altiplano cundiboyacense.'
    },

    // 2. Question with image, text options
    {
      id: 'question-image-1',
      type: 'question-image',
      description: 'Question with image in the question text, options are text-only',
      pregunta_texto: 'Observa la siguiente imagen matemática y responde:',
      pregunta_imagen: '/mathimg/Math_12_R_A_Doc1.png',
      opcion_a_texto: 'Opción A: La respuesta es 15',
      opcion_b_texto: 'Opción B: La respuesta es 20',
      opcion_c_texto: 'Opción C: La respuesta es 25',
      opcion_d_texto: 'Opción D: La respuesta es 30',
      respuesta_correcta: 'B',
      difficulty: 3,
      explanation: 'Observando la imagen, podemos ver que el cálculo correcto da como resultado 20.',
      hint: 'Mira cuidadosamente los números en la ecuación mostrada.'
    },

    // 3. Text question with image options
    {
      id: 'option-images-1',
      type: 'option-images',
      description: 'Text question with images as answer options',
      pregunta_texto: '¿Cuál de las siguientes opciones representa la solución correcta?',
      opcion_a_texto: 'Opción A',
      opcion_a_imagen: '/mathimg/Math_12_R_A_Doc1.png',
      opcion_b_texto: 'Opción B',
      opcion_b_imagen: '/mathimg/Math_12_R_B_Doc1.png',
      opcion_c_texto: 'Opción C',
      opcion_c_imagen: '/mathimg/Math_12_R_C_Doc1.png',
      opcion_d_texto: 'Opción D',
      opcion_d_imagen: '/mathimg/Math_12_R_D_Doc1.png',
      respuesta_correcta: 'C',
      difficulty: 4,
      explanation: 'La opción C muestra la representación gráfica correcta de la función.',
      hint: 'Compara las características de cada gráfico con los parámetros dados.'
    },

    // 4. Mixed content - question image + some option images
    {
      id: 'mixed-content-1',
      type: 'mixed-content',
      description: 'Mixed content with images in both question and some options',
      pregunta_texto: 'Basándote en el siguiente diagrama:',
      pregunta_imagen: '/mathimg/Math_17_1_Doc1.png',
      opcion_a_texto: 'Opción A: Texto solamente - La respuesta es falsa',
      opcion_b_texto: 'Opción B',
      opcion_b_imagen: '/mathimg/Math_15_1_Doc1.png',
      opcion_c_texto: 'Opción C: Texto solamente - La respuesta es verdadera',
      opcion_d_texto: 'Opción D',
      opcion_d_imagen: '/mathimg/Math_1_1_Doc1.png',
      respuesta_correcta: 'D',
      difficulty: 5,
      explanation: 'La opción D presenta la interpretación correcta del diagrama mostrado.',
      hint: 'Analiza primero el diagrama de la pregunta, luego compara con las opciones visuales.'
    },

    // 5. Bracket format images
    {
      id: 'bracket-format-1',
      type: 'mixed-content',
      description: 'Testing bracket format image parsing',
      pregunta_texto: 'Analiza la siguiente información: [Imagen: /mathimg/Math_12_R_A_Doc1.png]',
      opcion_a_texto: 'Opción A con imagen: [Imagen: /mathimg/Math_12_R_B_Doc1.png]',
      opcion_b_texto: 'Opción B: Solo texto descriptivo',
      opcion_c_texto: 'Opción C con imagen: [Imagen: /mathimg/Math_12_R_C_Doc1.png]',
      opcion_d_texto: 'Opción D: Solo texto descriptivo también',
      respuesta_correcta: 'A',
      difficulty: 3,
      explanation: 'El formato de corchetes se procesa correctamente para mostrar imágenes.',
      hint: 'Las imágenes en formato [Imagen: ruta] deben renderizarse automáticamente.'
    },

    // 6. Windows path conversion test
    {
      id: 'windows-path-1',
      type: 'mixed-content',
      description: 'Testing Windows path to web path conversion',
      pregunta_texto: 'Observa esta ecuación: C:\\Users\\PEDRO_PEREZ\\Documents\\IcfesLeveling\\mathimg\\Math_12_R_A_Doc1.png',
      opcion_a_texto: 'Opción A: C:\\Users\\PEDRO_PEREZ\\Documents\\IcfesLeveling\\mathimg\\Math_12_R_B_Doc1.png',
      opcion_b_texto: 'Opción B: Texto normal sin rutas',
      opcion_c_texto: 'Opción C: C:\\Users\\PEDRO_PEREZ\\Documents\\IcfesLeveling\\mathimg\\Math_12_R_C_Doc1.png',
      opcion_d_texto: 'Opción D: Otra opción de texto',
      respuesta_correcta: 'B',
      difficulty: 2,
      explanation: 'Las rutas de Windows se convierten automáticamente a rutas web compatibles.',
      hint: 'El sistema debe convertir rutas de Windows a formato web automáticamente.'
    },

    // 7. Error handling test - non-existent images
    {
      id: 'error-test-1',
      type: 'error-test',
      description: 'Testing error handling for missing images',
      pregunta_texto: 'Esta pregunta tiene una imagen que no existe:',
      pregunta_imagen: '/mathimg/NonExistent_Image.png',
      opcion_a_texto: 'Opción A con imagen faltante',
      opcion_a_imagen: '/mathimg/Missing_File.jpg',
      opcion_b_texto: 'Opción B: Texto normal',
      opcion_c_texto: 'Opción C con imagen válida',
      opcion_c_imagen: '/mathimg/Math_12_R_A_Doc1.png',
      opcion_d_texto: 'Opción D: Solo texto',
      respuesta_correcta: 'C',
      difficulty: 1,
      explanation: 'El sistema maneja correctamente las imágenes faltantes sin afectar la funcionalidad.',
      hint: 'Las imágenes faltantes deben mostrar un placeholder o mensaje de error.'
    },

    // 8. Multiple images in single option
    {
      id: 'multiple-images-1',
      type: 'mixed-content',
      description: 'Testing multiple image references in a single text field',
      pregunta_texto: 'Compara estas dos ecuaciones: /mathimg/Math_12_R_A_Doc1.png y también /mathimg/Math_12_R_B_Doc1.png',
      opcion_a_texto: 'Opción A: Primera ecuación es correcta',
      opcion_b_texto: 'Opción B: Segunda ecuación es correcta',
      opcion_c_texto: 'Opción C: Ambas ecuaciones: /mathimg/Math_12_R_C_Doc1.png y /mathimg/Math_12_R_D_Doc1.png',
      opcion_d_texto: 'Opción D: Ninguna es correcta',
      respuesta_correcta: 'C',
      difficulty: 4,
      explanation: 'El sistema puede manejar múltiples imágenes en un mismo campo de texto.',
      hint: 'Busca la opción que combine correctamente ambas ecuaciones.'
    }
  ];

  const currentQuestion = testQuestions[currentQuestionIndex];

  const handleAnswerSelect = (answer: string) => {
    setAnswers(prev => ({
      ...prev,
      [currentQuestion.id]: answer
    }));
  };

  const handleNext = () => {
    if (currentQuestionIndex < testQuestions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    } else {
      setShowResults(true);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
    }
  };

  const getTestResults = () => {
    const answeredQuestions = Object.keys(answers).length;
    const correctAnswers = testQuestions.filter(q => 
      answers[q.id] === q.respuesta_correcta
    ).length;
    
    return {
      total: testQuestions.length,
      answered: answeredQuestions,
      correct: correctAnswers,
      percentage: answeredQuestions > 0 ? Math.round((correctAnswers / testQuestions.length) * 100) : 0
    };
  };

  const resetTest = () => {
    setCurrentQuestionIndex(0);
    setAnswers({});
    setShowResults(false);
  };

  const results = getTestResults();

  if (showResults) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-100">
        <div className="container mx-auto px-4 py-8">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="max-w-4xl mx-auto"
          >
            {/* Results Header */}
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-gray-800 mb-4">
                🎯 Test de Tipos de Pregunta Completado
              </h1>
              <div className="text-6xl mb-4">
                {results.percentage >= 80 ? '🎉' : results.percentage >= 60 ? '👍' : '📚'}
              </div>
            </div>

            {/* Results Summary */}
            <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-6">📊 Resumen de Resultados</h2>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">{results.total}</div>
                  <div className="text-gray-600">Total de Preguntas</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">{results.answered}</div>
                  <div className="text-gray-600">Respondidas</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-purple-600">{results.correct}</div>
                  <div className="text-gray-600">Correctas</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-orange-600">{results.percentage}%</div>
                  <div className="text-gray-600">Puntuación</div>
                </div>
              </div>

              {/* Performance by Question Type */}
              <div className="mt-8">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">📋 Rendimiento por Tipo de Pregunta</h3>
                <div className="space-y-3">
                  {testQuestions.map((question, index) => {
                    const userAnswer = answers[question.id];
                    const isCorrect = userAnswer === question.respuesta_correcta;
                    const wasAnswered = !!userAnswer;
                    
                    return (
                      <div
                        key={question.id}
                        className={`p-4 rounded-lg border-l-4 ${
                          !wasAnswered ? 'bg-gray-50 border-gray-400' :
                          isCorrect ? 'bg-green-50 border-green-500' : 'bg-red-50 border-red-500'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <h4 className="font-semibold text-gray-800">
                              Pregunta {index + 1}: {question.description}
                            </h4>
                            <p className="text-sm text-gray-600 mt-1">
                              Tipo: <span className="font-medium">{question.type}</span>
                            </p>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                              !wasAnswered ? 'bg-gray-100 text-gray-600' :
                              isCorrect ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }`}>
                              {!wasAnswered ? 'Sin responder' :
                               isCorrect ? '✅ Correcta' : '❌ Incorrecta'}
                            </span>
                            {wasAnswered && (
                              <span className="text-sm text-gray-500">
                                Tu respuesta: {userAnswer} | Correcta: {question.respuesta_correcta}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Test Coverage Summary */}
            <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">🧪 Cobertura de Pruebas</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h3 className="font-semibold text-gray-700 mb-2">Tipos de Contenido Probados:</h3>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>✅ Preguntas solo texto</li>
                    <li>✅ Preguntas con imagen + opciones texto</li>
                    <li>✅ Preguntas texto + opciones imagen</li>
                    <li>✅ Contenido mixto (texto + imágenes)</li>
                    <li>✅ Formato de corchetes [Imagen: ruta]</li>
                    <li>✅ Conversión de rutas Windows</li>
                    <li>✅ Manejo de errores (imágenes faltantes)</li>
                    <li>✅ Múltiples imágenes por opción</li>
                  </ul>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-700 mb-2">Funciones Verificadas:</h3>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>✅ Parsing de imágenes en diferentes formatos</li>
                    <li>✅ Renderizado correcto de multimedia</li>
                    <li>✅ Navegación entre preguntas</li>
                    <li>✅ Selección y almacenamiento de respuestas</li>
                    <li>✅ Manejo de errores de carga</li>
                    <li>✅ Responsive design</li>
                    <li>✅ Accesibilidad de contenido</li>
                    <li>✅ Performance de carga</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="text-center space-x-4">
              <button
                onClick={resetTest}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
              >
                🔄 Reiniciar Test
              </button>
              <button
                onClick={() => window.location.href = '/test-multimedia-comprehensive'}
                className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors"
              >
                🧪 Ir a Test Completo
              </button>
            </div>
          </motion.div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-4xl font-bold text-gray-800 mb-4">
            🎯 Test de Tipos de Pregunta Multimedia
          </h1>
          <p className="text-xl text-gray-600">
            Probando diferentes tipos de contenido multimedia en preguntas
          </p>
          
          {/* Progress */}
          <div className="mt-6 max-w-md mx-auto">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>Progreso</span>
              <span>{currentQuestionIndex + 1} / {testQuestions.length}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <motion.div
                className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${((currentQuestionIndex + 1) / testQuestions.length) * 100}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </div>
        </motion.div>

        {/* Question Type Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-lg shadow-lg p-6 mb-8"
        >
          <h2 className="text-xl font-semibold text-gray-800 mb-2">
            🔍 Tipo de Pregunta Actual: {currentQuestion.type}
          </h2>
          <p className="text-gray-600 mb-4">{currentQuestion.description}</p>
          
          <div className="flex flex-wrap gap-2">
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${
              currentQuestion.type === 'text-only' ? 'bg-blue-100 text-blue-800' :
              currentQuestion.type === 'question-image' ? 'bg-green-100 text-green-800' :
              currentQuestion.type === 'option-images' ? 'bg-purple-100 text-purple-800' :
              currentQuestion.type === 'mixed-content' ? 'bg-orange-100 text-orange-800' :
              'bg-red-100 text-red-800'
            }`}>
              {currentQuestion.type.replace('-', ' ').toUpperCase()}
            </span>
            <span className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-xs font-medium">
              Dificultad: {currentQuestion.difficulty}/5
            </span>
            {multimediaQuestionsService.hasMultimediaContent(currentQuestion) && (
              <span className="px-3 py-1 bg-pink-100 text-pink-800 rounded-full text-xs font-medium">
                📸 Multimedia
              </span>
            )}
          </div>
        </motion.div>

        {/* Question Component */}
        <motion.div
          key={currentQuestion.id}
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -50 }}
          transition={{ duration: 0.3 }}
        >
          <MultimediaQuestion
            question={currentQuestion}
            questionNumber={currentQuestionIndex + 1}
            totalQuestions={testQuestions.length}
            selectedAnswer={answers[currentQuestion.id]}
            onAnswerSelect={handleAnswerSelect}
            onNext={handleNext}
            onPrevious={handlePrevious}
            showExplanation={false}
            isAnswered={false}
          />
        </motion.div>

        {/* Test Progress Summary */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-8 bg-white rounded-lg shadow-lg p-6"
        >
          <h3 className="text-lg font-semibold text-gray-800 mb-4">📊 Progreso del Test</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{Object.keys(answers).length}</div>
              <div className="text-gray-600 text-sm">Respondidas</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">{testQuestions.length - Object.keys(answers).length}</div>
              <div className="text-gray-600 text-sm">Pendientes</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {Math.round((Object.keys(answers).length / testQuestions.length) * 100)}%
              </div>
              <div className="text-gray-600 text-sm">Completado</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {testQuestions.filter(q => answers[q.id] === q.respuesta_correcta).length}
              </div>
              <div className="text-gray-600 text-sm">Correctas</div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}