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
    // Fetch subjects from API
    fetch('http://localhost:4000/api/v1/subjects/dynamic')
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
            {subjects.map((subject) => (
              <div
                key={subject.id}
                className="bg-black/40 backdrop-blur-sm border border-purple-500/50 hover:border-yellow-400 rounded-lg p-6 cursor-pointer transform hover:scale-105 transition-all duration-300 hover:shadow-[0_0_20px_#ffd700]"
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
                      <span>⚔️ Combates:</span>
                      <span className="font-medium text-purple-300">
                        {subject.config?.total_questions || 45}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>⏱️ Tiempo:</span>
                      <span className="font-medium text-purple-300">
                        {subject.config?.time_limit_minutes || 60} min
                      </span>
                    </div>
                  </div>
                  
                  {/* Start Button */}
                  <button 
                    className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-3 px-4 rounded-lg transition-all duration-300 transform hover:scale-105 shadow-lg"
                    onClick={(e) => {
                      e.stopPropagation();
                      startDiagnostic(subject);
                    }}
                  >
                    ⚔️ Iniciar Diagnóstico
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Success Message */}
        <div className="text-center bg-green-900/50 rounded-lg p-6 border border-green-500">
          <h2 className="text-green-400 font-bold text-xl mb-2">
            ✅ ¡SISTEMA DINÁMICO DE DIAGNÓSTICO ACTIVO!
          </h2>
          <p className="text-green-300">
            {subjects.length} materias cargadas dinámicamente desde la base de datos.
          </p>
          <p className="text-green-200 text-sm mt-2">
            🚀 Sistema inteligente con configuración dinámica y gestión de assets
          </p>
        </div>
      </div>
    </div>
  );
}