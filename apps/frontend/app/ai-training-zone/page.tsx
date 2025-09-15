'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  AcademicCapIcon, 
  ChartBarIcon, 
  SparklesIcon,
  BookOpenIcon,
  PlayIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline';
import IntelligentTrainingZone from '../components/AITrainingZone/IntelligentTrainingZone';
import AIProgressDashboard from '../components/AITrainingZone/AIProgressDashboard';
import AITutor from '../components/AITrainingZone/AITutor';

interface Subject {
  id: number;
  name: string;
  description: string;
}

export default function AITrainingZonePage() {
  const [selectedView, setSelectedView] = useState<'training' | 'progress' | 'tutor'>('training');
  const [selectedSubject, setSelectedSubject] = useState<number | null>(null);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [trainingSettings, setTrainingSettings] = useState({
    questionCount: 10,
    adaptiveDifficulty: true,
    focusAreas: [] as string[],
    timeLimit: false
  });

  useEffect(() => {
    fetchSubjects();
  }, []);

  const fetchSubjects = async () => {
    try {
      const response = await fetch('/api/subjects', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setSubjects(data);
        if (data.length > 0) {
          setSelectedSubject(data[0].id);
        }
      }
    } catch (error) {
      console.error('Error fetching subjects:', error);
    }
  };

  const handleRecommendationClick = (recommendation: string) => {
    // Parse recommendation to determine action
    if (recommendation.includes('practicar') || recommendation.includes('ejercicios')) {
      setSelectedView('training');
    } else if (recommendation.includes('concepto') || recommendation.includes('explicación')) {
      setSelectedView('tutor');
    }
    // Could add more intelligent routing based on recommendation content
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg">
                <SparklesIcon className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                  Zona de Entrenamiento IA
                </h1>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Entrenamiento inteligente personalizado para ICFES
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {/* Subject selector */}
              <select
                value={selectedSubject || ''}
                onChange={(e) => setSelectedSubject(parseInt(e.target.value))}
                className="text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-gray-900 dark:text-white"
              >
                <option value="">Seleccionar materia</option>
                {subjects.map(subject => (
                  <option key={subject.id} value={subject.id}>
                    {subject.name}
                  </option>
                ))}
              </select>

              {/* Settings button */}
              <button
                onClick={() => {/* TODO: Open settings modal */}}
                className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                title="Configuración"
              >
                <Cog6ToothIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation tabs */}
      <div className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8" aria-label="Tabs">
            <button
              onClick={() => setSelectedView('training')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                selectedView === 'training'
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center space-x-2">
                <PlayIcon className="h-4 w-4" />
                <span>Entrenamiento</span>
              </div>
            </button>

            <button
              onClick={() => setSelectedView('progress')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                selectedView === 'progress'
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center space-x-2">
                <ChartBarIcon className="h-4 w-4" />
                <span>Progreso IA</span>
              </div>
            </button>

            <button
              onClick={() => setSelectedView('tutor')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                selectedView === 'tutor'
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center space-x-2">
                <AcademicCapIcon className="h-4 w-4" />
                <span>Tutor IA</span>
              </div>
            </button>
          </nav>
        </div>
      </div>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <motion.div
          key={selectedView}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
        >
          {selectedView === 'training' && selectedSubject && (
            <IntelligentTrainingZone
              subjectId={selectedSubject}
              initialQuestionCount={trainingSettings.questionCount}
              adaptiveDifficulty={trainingSettings.adaptiveDifficulty}
              focusAreas={trainingSettings.focusAreas}
            />
          )}

          {selectedView === 'progress' && (
            <AIProgressDashboard
              subjectId={selectedSubject}
              onRecommendationClick={handleRecommendationClick}
            />
          )}

          {selectedView === 'tutor' && (
            <div className="max-w-4xl mx-auto">
              <div className="bg-white dark:bg-gray-900 rounded-xl shadow-lg p-6 mb-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                  Tutor IA Personalizado
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  Chatea con tu tutor de IA especializado en ICFES. Pregunta sobre conceptos, estrategias, 
                  o cualquier duda que tengas. El tutor se adapta a tu nivel y necesidades específicas.
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
                      Explicaciones personalizadas
                    </h3>
                    <p className="text-sm text-blue-700 dark:text-blue-300">
                      Recibe explicaciones adaptadas a tu nivel de comprensión
                    </p>
                  </div>
                  
                  <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <h3 className="font-semibold text-green-900 dark:text-green-100 mb-2">
                      Estrategias inteligentes
                    </h3>
                    <p className="text-sm text-green-700 dark:text-green-300">
                      Obtén estrategias específicas basadas en tu rendimiento
                    </p>
                  </div>
                  
                  <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                    <h3 className="font-semibold text-purple-900 dark:text-purple-100 mb-2">
                      Apoyo 24/7
                    </h3>
                    <p className="text-sm text-purple-700 dark:text-purple-300">
                      Disponible siempre que necesites ayuda con tus estudios
                    </p>
                  </div>
                </div>
              </div>

              <div className="h-96">
                <AITutor
                  studentId="current_user"
                  subjectId={selectedSubject}
                  initialContext="concept_review"
                  onInteraction={(interaction) => {
                    console.log('Tutor interaction:', interaction);
                  }}
                />
              </div>
            </div>
          )}

          {selectedView === 'training' && !selectedSubject && (
            <div className="text-center py-12">
              <BookOpenIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Selecciona una materia
              </h3>
              <p className="text-gray-500 dark:text-gray-400 mb-6">
                Elige una materia para comenzar tu entrenamiento personalizado con IA
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-4xl mx-auto">
                {subjects.map(subject => (
                  <motion.button
                    key={subject.id}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setSelectedSubject(subject.id)}
                    className="p-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl hover:border-blue-500 dark:hover:border-blue-400 transition-colors text-left"
                  >
                    <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                      {subject.name}
                    </h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {subject.description || 'Entrenamiento inteligente personalizado'}
                    </p>
                  </motion.button>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      </div>

      {/* Quick stats footer */}
      <div className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">IA</div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Tutoring personalizado</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">24/7</div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Disponibilidad</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">∞</div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Preguntas ilimitadas</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">🎯</div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Entrenamiento adaptativo</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}