'use client';

import { useState, useEffect } from 'react';
import DynamicSubjectIcon from '../../components/DynamicSubjectIcon';
import DiagnosticTestFlow from './test-flow';

export default function DiagnosticTest() {
  const [subjects, setSubjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSubject, setSelectedSubject] = useState<any>(null);

  useEffect(() => {
    // Fetch subjects with IMAGE questions ONLY for testing
    import('../lib/dynamic-config').then(({ buildApiUrl }) => 
      fetch(buildApiUrl('/diagnostic-images-test/subjects-with-image-questions'))
    )
      .then(res => res.json())
      .then(data => {
        setSubjects(data || []);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching subjects:', err);
        setError('No se pudieron cargar las materias desde la base de datos');
        setLoading(false);
      });
  }, []);

  const startDiagnostic = (subject: any) => {
    // Check if subject is available
    if (!subject.is_available) {
      alert(`❌ ${subject.name} no está disponible\n\n${subject.availability_message}`);
      return;
    }
    
    // Warn if limited questions
    if (subject.availability_status === 'limited') {
      const confirmStart = confirm(`⚠️ ${subject.name} tiene pocas preguntas disponibles\n\n${subject.availability_message}\n\n¿Deseas continuar de todos modos?`);
      if (!confirmStart) {
        return;
      }
    }
    
    setSelectedSubject(subject);
  };

  const handleTestComplete = (results: any) => {
    alert(`
🎯 Test Completado!
📊 Resultado: ${results.score_percentage}%
✅ Respuestas Correctas: ${results.correct_answers}/${results.total_questions}
⏱️ Tiempo: ${Math.floor(results.time_spent / 60)} minutos

¡Excelente trabajo! Tu plan de estudio personalizado está listo.
    `);
    setSelectedSubject(null);
  };

  // If a subject is selected, show the test interface
  if (selectedSubject) {
    return (
      <DiagnosticTestFlow
        subjectId={selectedSubject.id}
        subjectName={selectedSubject.name}
        onComplete={handleTestComplete}
      />
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-black to-purple-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-white text-lg">Cargando materias dinámicamente...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-black to-red-900 flex items-center justify-center">
        <div className="text-center bg-red-900/50 p-8 rounded-lg">
          <h1 className="text-2xl font-bold text-red-400 mb-4">❌ Error de Conexión</h1>
          <p className="text-red-300">{error}</p>
          <p className="text-red-200 text-sm mt-2">No se pudieron cargar las materias dinámicamente</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-black to-purple-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-yellow-400 mb-4">
            🏰 Academia de Hunters ICFES
          </h1>
          <p className="text-xl text-purple-300">
            Inicia tu viaje épico hacia la conquista del conocimiento
          </p>
          <div className="mt-4 flex justify-center gap-4">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-900 text-purple-300 border border-purple-500">
              🏆 Sistema Adaptativo IA
            </span>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-900 text-purple-300 border border-purple-500">
              ⚔️ Gamificación Épica
            </span>
          </div>
        </div>

        {/* Main Content */}
        <div className="bg-black/30 backdrop-blur-md rounded-lg border border-purple-500 p-6 mb-8">
          <div className="mb-6 text-center">
            <h3 className="text-2xl font-bold text-yellow-400 mb-2">
              ⚔️ Elige tu Primera Conquista
            </h3>
            <p className="text-purple-300">
              Comenzarás con un diagnóstico místico para evaluar tu poder actual
            </p>
          </div>

          {/* Subjects Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {subjects.map((subject) => {
              const isUnavailable = !subject.is_available;
              const isLimited = subject.availability_status === 'limited';
              
              return (
              <div
                key={subject.id}
                className={`bg-black/40 backdrop-blur-sm border rounded-lg p-6 transition-all duration-300 ${
                  isUnavailable 
                    ? 'border-gray-600/50 opacity-50 cursor-not-allowed grayscale' 
                    : isLimited
                    ? 'border-yellow-500/50 hover:border-yellow-400 cursor-pointer transform hover:scale-105 hover:shadow-[0_0_20px_#fbbf24]'
                    : 'border-purple-500/50 hover:border-yellow-400 cursor-pointer transform hover:scale-105 hover:shadow-[0_0_20px_#ffd700]'
                }`}
                onClick={() => startDiagnostic(subject)}
              >
                <div className="text-center">
                  {/* Dynamic Subject Icon */}
                  <div 
                    className="w-20 h-20 mx-auto mb-4 rounded-full flex items-center justify-center shadow-lg"
                    style={{ backgroundColor: subject.display?.color_primary || subject.color || '#8B5CF6' }}
                  >
                    <DynamicSubjectIcon 
                      subjectId={subject.id}
                      subjectName={subject.name}
                      size={48}
                      className="text-white"
                    />
                  </div>
                  
                  {/* Subject Title */}
                  <h3 className="text-xl font-bold text-yellow-400 mb-2">
                    {subject.name}
                  </h3>
                  
                  {/* Subject Description */}
                  <p className="text-purple-300 mb-4 text-sm">
                    {subject.display?.description_short || subject.description || 'Conquista esta materia'}
                  </p>
                  
                  {/* Subject Details */}
                  <div className="space-y-2 text-sm text-gray-400 mb-4">
                    <div className="flex justify-between">
                      <span>🖼️ Preguntas con Imágenes:</span>
                      <span className="font-medium text-purple-300">
                        {subject.available_for_test || subject.config?.total_questions || 20}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>⏱️ Tiempo:</span>
                      <span className="font-medium text-purple-300">
                        {subject.config?.time_limit_minutes || 30} min
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>📊 Total disponibles:</span>
                      <span className="font-medium text-yellow-300">
                        {subject.image_question_count || 0}
                      </span>
                    </div>
                  </div>
                  
                  {/* Availability Status */}
                  <div className="mb-4">
                    {isUnavailable ? (
                      <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-2">
                        <p className="text-red-300 text-sm">❌ No disponible</p>
                        <p className="text-red-400 text-xs">{subject.availability_message}</p>
                      </div>
                    ) : isLimited ? (
                      <div className="bg-yellow-900/30 border border-yellow-500/30 rounded-lg p-2">
                        <p className="text-yellow-300 text-sm">⚠️ Disponibilidad limitada</p>
                        <p className="text-yellow-400 text-xs">{subject.availability_message}</p>
                      </div>
                    ) : (
                      <div className="bg-green-900/30 border border-green-500/30 rounded-lg p-2">
                        <p className="text-green-300 text-sm">✅ Disponible</p>
                        <p className="text-green-400 text-xs">{subject.availability_message}</p>
                      </div>
                    )}
                  </div>
                  
                  {/* Start Button */}
                  <button 
                    className={`w-full font-bold py-3 px-4 rounded-lg transition-all duration-300 ${
                      isUnavailable 
                        ? 'bg-gray-600 text-gray-400 cursor-not-allowed' 
                        : isLimited
                        ? 'bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-700 hover:to-orange-700 text-white transform hover:scale-105 shadow-lg'
                        : 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white transform hover:scale-105 shadow-lg'
                    }`}
                    onClick={(e) => {
                      e.stopPropagation();
                      startDiagnostic(subject);
                    }}
                    disabled={isUnavailable}
                  >
                    {isUnavailable ? '❌ No Disponible' : isLimited ? '⚠️ Iniciar (Pocas Preguntas)' : '⚔️ Iniciar Diagnóstico'}
                  </button>
                </div>
              </div>
              );
            })}
          </div>
        </div>

        {/* System Status Message */}
        <div className="text-center bg-blue-900/50 rounded-lg p-6 border border-blue-500">
          <h2 className="text-blue-400 font-bold text-xl mb-2">
            🖼️ ¡MODO TESTING CON PREGUNTAS DE IMÁGENES ÚNICAMENTE!
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="bg-green-800/30 p-3 rounded">
              <p className="text-green-300 font-semibold">Materias con Imágenes</p>
              <p className="text-green-200">{subjects.filter(s => s.availability_status === 'available').length}</p>
            </div>
            <div className="bg-yellow-800/30 p-3 rounded">
              <p className="text-yellow-300 font-semibold">Disponibilidad Limitada</p>
              <p className="text-yellow-200">{subjects.filter(s => s.availability_status === 'limited').length}</p>
            </div>
            <div className="bg-blue-800/30 p-3 rounded">
              <p className="text-blue-300 font-semibold">Total Preguntas Imagen</p>
              <p className="text-blue-200">{subjects.reduce((sum, s) => sum + (s.image_question_count || 0), 0)}</p>
            </div>
          </div>
          <p className="text-blue-200 text-sm mt-4">
            📸 Solo se mostrarán preguntas que requieren imágenes • Máximo 20 por materia
          </p>
        </div>
      </div>
    </div>
  );
}