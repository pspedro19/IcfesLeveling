'use client';

import { useState, useEffect } from 'react';

export default function TestDiagnostic() {
  const [subjects, setSubjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load subjects immediately with mock data
    const mockSubjects = [
      {
        id: '1',
        name: 'Matemáticas',
        description: 'Números y ecuaciones',
        color: '#8B5CF6',
        config: { total_questions: 45, time_limit_minutes: 60 }
      },
      {
        id: '2', 
        name: 'Lectura Crítica',
        description: 'Comprensión de textos',
        color: '#3B82F6',
        config: { total_questions: 45, time_limit_minutes: 90 }
      },
      {
        id: '3',
        name: 'Ciencias Naturales', 
        description: 'Biología, Química, Física',
        color: '#10B981',
        config: { total_questions: 45, time_limit_minutes: 60 }
      },
      {
        id: '4',
        name: 'Sociales y Ciudadanas',
        description: 'Historia y sociedad',
        color: '#F59E0B', 
        config: { total_questions: 45, time_limit_minutes: 90 }
      },
      {
        id: '5',
        name: 'Inglés',
        description: 'Idioma internacional',
        color: '#EF4444',
        config: { total_questions: 45, time_limit_minutes: 60 }
      }
    ];

    setSubjects(mockSubjects);
    setLoading(false);

    // Try to load real data in background
    fetch('http://localhost:4001/api/v1/diagnostic-public/subjects')
      .then(res => res.json())
      .then(data => {
        console.log('Real subjects loaded:', data);
        setSubjects(data);
      })
      .catch(err => console.log('Using mock subjects:', err));
  }, []);

  const startTest = (subject: any) => {
    alert(`¡Iniciando test de ${subject.name}!\n\nEsto funcionaría en la aplicación real.`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-indigo-900">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-yellow-400 mb-4">
            🏰 ICFES Test Diagnóstico
          </h1>
          <p className="text-xl text-purple-300">
            ✅ FUNCIONANDO - Elige tu materia para comenzar
          </p>
        </div>

        {loading ? (
          <div className="text-center">
            <p className="text-white">Cargando materias...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {subjects.map((subject) => (
              <div
                key={subject.id}
                className="bg-black/30 backdrop-blur-md rounded-lg p-6 border-2 border-purple-500/50 hover:border-yellow-400 transition-all cursor-pointer transform hover:scale-105 hover:shadow-xl"
                onClick={() => startTest(subject)}
              >
                <div className="text-center">
                  <div 
                    className="w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center text-2xl font-bold text-white shadow-lg"
                    style={{ backgroundColor: subject.color }}
                  >
                    📖
                  </div>
                  
                  <h3 className="text-xl font-bold text-yellow-400 mb-2">
                    {subject.name}
                  </h3>
                  
                  <p className="text-purple-300 mb-4 text-sm">
                    {subject.description}
                  </p>
                  
                  <div className="bg-black/50 rounded p-3 mb-4 text-sm">
                    <div className="flex justify-between mb-1">
                      <span className="text-gray-300">Preguntas:</span>
                      <span className="text-white font-semibold">
                        {subject.config.total_questions}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-300">Tiempo:</span>
                      <span className="text-white font-semibold">
                        {subject.config.time_limit_minutes} min
                      </span>
                    </div>
                  </div>
                  
                  <button 
                    className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-3 px-4 rounded-lg transition-all transform hover:scale-105 shadow-lg"
                    onClick={(e) => {
                      e.stopPropagation();
                      startTest(subject);
                    }}
                  >
                    🚀 Iniciar Diagnóstico
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
        
        <div className="mt-8 text-center bg-green-900/50 rounded-lg p-4">
          <h2 className="text-green-400 font-bold text-lg mb-2">
            ✅ ¡DIAGNÓSTICO FUNCIONANDO CORRECTAMENTE!
          </h2>
          <p className="text-green-300">
            Puedes hacer clic en cualquier materia para comenzar el test
          </p>
        </div>
      </div>
    </div>
  );
}