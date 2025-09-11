'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

// 🚀 PORTAL DEL DESPERTAR - MVP Funcional
export default function PortalDelDespertar() {
  const [selectedSubject, setSelectedSubject] = useState<string | null>(null);
  const [hunterLevel, setHunterLevel] = useState(1);
  const [currentRank, setCurrentRank] = useState('E');
  const [isAwakening, setIsAwakening] = useState(false);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  // Load real subjects from database
  useEffect(() => {
    const fetchSubjects = async () => {
      try {
        setLoading(true);
        const response = await fetch('http://localhost:4000/api/v1/subjects/dynamic');
        if (!response.ok) {
          throw new Error('Failed to fetch subjects');
        }
        const data = await response.json();
        
        // Transform data to match our UI needs
        const transformedSubjects = data.map((subject: any) => ({
          id: subject.id,
          name: subject.name,
          description: subject.description || `Evaluación de competencias en ${subject.name}`,
          icon: getSubjectIcon(subject.name),
          color: subject.display?.color_primary || getSubjectColor(subject.name),
          guardian: getSubjectGuardian(subject.name),
          difficulty: getDifficultyLevel(subject.question_count),
          questions: subject.question_count || 0
        }));
        
        setSubjects(transformedSubjects);
        setError(null);
      } catch (err) {
        console.error('Error fetching subjects:', err);
        setError('No se pudieron cargar las materias desde la base de datos');
        // Fallback to some basic subjects if API fails
        setSubjects([
          {
            id: "fallback",
            name: "Matemáticas",
            description: "Evaluación básica (modo offline)",
            icon: "🔢",
            color: "#FF6B6B",
            guardian: "Guardián de los Números",
            difficulty: "Medio",
            questions: 0
          }
        ]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchSubjects();
  }, []);
  
  // Helper functions for subject customization
  const getSubjectIcon = (name: string) => {
    const icons: {[key: string]: string} = {
      'matemáticas': '🔢',
      'matematicas': '🔢',
      'física': '⚛️',
      'fisica': '⚛️',
      'química': '🧪',
      'quimica': '🧪',
      'biología': '🧬',
      'biologia': '🧬',
      'español': '📚',
      'lenguaje': '📚',
      'lectura crítica': '📖',
      'lectura critica': '📖',
      'ciencias naturales': '🔬',
      'sociales': '🌍',
      'inglés': '🇺🇸',
      'ingles': '🇺🇸',
      'filosofía': '🤔',
      'filosofia': '🤔'
    };
    return icons[name.toLowerCase()] || '📚';
  };
  
  const getSubjectColor = (name: string) => {
    const colors: {[key: string]: string} = {
      'matemáticas': '#FF6B6B',
      'matematicas': '#FF6B6B',
      'física': '#4ECDC4',
      'fisica': '#4ECDC4',
      'química': '#45B7D1',
      'quimica': '#45B7D1',
      'biología': '#96CEB4',
      'biologia': '#96CEB4',
      'español': '#FFEAA7',
      'lenguaje': '#FFEAA7',
      'lectura crítica': '#DDA0DD',
      'lectura critica': '#DDA0DD',
      'ciencias naturales': '#98FB98',
      'sociales': '#F4A460',
      'inglés': '#87CEEB',
      'ingles': '#87CEEB',
      'filosofía': '#D8BFD8',
      'filosofia': '#D8BFD8'
    };
    return colors[name.toLowerCase()] || '#8B5CF6';
  };
  
  const getSubjectGuardian = (name: string) => {
    const guardians: {[key: string]: string} = {
      'matemáticas': 'Guardián de los Números',
      'matematicas': 'Guardián de los Números',
      'física': 'Guardián de las Fuerzas',
      'fisica': 'Guardián de las Fuerzas',
      'química': 'Guardián de los Elementos',
      'quimica': 'Guardián de los Elementos',
      'biología': 'Guardián de la Vida',
      'biologia': 'Guardián de la Vida',
      'español': 'Guardián de las Palabras',
      'lenguaje': 'Guardián de las Palabras',
      'lectura crítica': 'Guardián de la Comprensión',
      'lectura critica': 'Guardián de la Comprensión',
      'ciencias naturales': 'Guardián del Cosmos',
      'sociales': 'Guardián de la Historia',
      'inglés': 'Guardián de las Lenguas',
      'ingles': 'Guardián de las Lenguas',
      'filosofía': 'Guardián de la Sabiduría',
      'filosofia': 'Guardián de la Sabiduría'
    };
    return guardians[name.toLowerCase()] || 'Guardián del Conocimiento';
  };
  
  const getDifficultyLevel = (questionCount: number) => {
    if (questionCount === 0) return 'Sin Preguntas';
    if (questionCount < 10) return 'Bajo';
    if (questionCount < 50) return 'Medio';
    if (questionCount < 100) return 'Alto';
    return 'Épico';
  };

  const ranks = {
    'E': { name: 'Aspirante a Cazador', color: '#FFEAA7', icon: '🔰' },
    'D': { name: 'Cazador Novato', color: '#96CEB4', icon: '⚔️' },
    'C': { name: 'Cazador Competente', color: '#45B7D1', icon: '🛡️' },
    'B': { name: 'Cazador Avanzado', color: '#4ECDC4', icon: '⚡' },
    'A': { name: 'Cazador Elite', color: '#FF6B35', icon: '🔥' },
    'S': { name: 'Monarca del Conocimiento', color: '#FFD700', icon: '👑' }
  };

  const handleSubjectSelect = (subject: any) => {
    // Directamente seleccionar la materia sin redirección
    setSelectedSubject(subject.id);
    setIsAwakening(false); // No mostrar animación de despertar
  };

  const handleReturnToHub = () => {
    router.push('/student-dashboard');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center space-y-6">
          <div className="text-8xl mb-4">🌟</div>
          <h1 className="text-4xl font-bold text-gold-400 mb-4">
            CARGANDO PORTAL DEL DESPERTAR
          </h1>
          <div className="text-2xl text-white">
            Conectando con la base de datos de materias...
          </div>
          <div className="flex justify-center space-x-2 mt-8">
            <div className="w-4 h-4 bg-gold-400 rounded-full animate-bounce"></div>
            <div className="w-4 h-4 bg-gold-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
            <div className="w-4 h-4 bg-gold-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
          </div>
        </div>
      </div>
    );
  }

  // Si se seleccionó una materia, mostrar el test interface
  if (selectedSubject) {
    const TestInterface = require('../diagnostic-test/test-interface').default;
    const selectedSubjectData = subjects.find(s => s.id === selectedSubject);
    
    const handleTestComplete = (results: any) => {
      alert(`
🎯 Test Completado!
📊 Resultado: ${results.score_percentage}%
✅ Respuestas Correctas: ${results.correct_answers}/${results.total_questions}
⏱️ Tiempo: ${Math.floor(results.time_spent / 60)} minutos

¡Excelente trabajo! Tu plan de estudio personalizado está listo.
      `);
      setSelectedSubject(null); // Volver a la selección de materias
    };
    
    return (
      <TestInterface
        subjectId={selectedSubject}
        subjectName={selectedSubjectData?.name || 'Materia'}
        onComplete={handleTestComplete}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
      {/* Header Epic */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-purple-600/20 to-blue-600/20"></div>
        <div className="relative z-10 text-center py-16 px-4">
          <div className="text-8xl mb-4">🌟</div>
          <h1 className="text-6xl font-bold mb-4 bg-gradient-to-r from-gold-400 to-purple-400 bg-clip-text text-transparent">
            PORTAL DEL DESPERTAR
          </h1>
          <p className="text-2xl text-gray-300 max-w-4xl mx-auto leading-relaxed">
            "En las profundidades del conocimiento yacen poderes inimaginables. 
            Solo aquellos valientes que se atrevan a enfrentar sus debilidades 
            podrán despertar como verdaderos <span className="text-gold-400 font-bold">Cazadores del Conocimiento ICFES</span>."
          </p>
          
          {/* Hunter Status */}
          <div className="mt-8 bg-black/30 backdrop-blur-sm rounded-lg p-6 max-w-md mx-auto border border-purple-500/30">
            <div className="flex items-center justify-center space-x-4">
              <div className="text-4xl">{ranks[currentRank as keyof typeof ranks]?.icon}</div>
              <div>
                <div className="text-sm text-gray-400">Rango Actual</div>
                <div className="text-2xl font-bold" style={{color: ranks[currentRank as keyof typeof ranks]?.color}}>
                  {currentRank} - {ranks[currentRank as keyof typeof ranks]?.name}
                </div>
                <div className="text-sm text-gray-400">Nivel {hunterLevel}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Selección de Materias */}
      <div className="container mx-auto px-4 py-12">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold mb-4 text-gold-400">
            ⚔️ Escoge tu Camino del Despertar
          </h2>
          <p className="text-xl text-gray-300">
            Cada materia tiene su propio Guardián. Derrótalo para despertar tus habilidades.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {subjects.map((subject) => (
            <div
              key={subject.id}
              className="group relative bg-black/40 backdrop-blur-sm rounded-xl p-6 border border-purple-500/30 hover:border-gold-400/50 transition-all duration-300 cursor-pointer hover:transform hover:scale-105"
              onClick={() => handleSubjectSelect(subject)}
              style={{boxShadow: `0 0 20px ${subject.color}20`}}
            >
              {/* Subject Icon */}
              <div className="text-center mb-6">
                <div className="text-6xl mb-2">{subject.icon}</div>
                <h3 className="text-2xl font-bold" style={{color: subject.color}}>
                  {subject.name}
                </h3>
              </div>

              {/* Guardian Info */}
              <div className="space-y-4">
                <div className="text-center">
                  <div className="text-lg font-bold text-gold-400 mb-1">
                    🗡️ {subject.guardian}
                  </div>
                  <div className="text-sm text-gray-400">
                    {subject.description}
                  </div>
                </div>

                {/* Stats */}
                <div className="flex justify-between items-center text-sm">
                  <div className="flex items-center space-x-1">
                    <span className="text-red-400">⚡</span>
                    <span>Dificultad: {subject.difficulty}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <span className="text-blue-400">❓</span>
                    <span>{subject.questions} preguntas</span>
                  </div>
                </div>

                {/* Action Button */}
                <button className="w-full py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 rounded-lg font-bold text-lg transition-all duration-300 group-hover:shadow-lg">
                  🌟 INICIAR DESPERTAR
                </button>
              </div>

              {/* Glow Effect */}
              <div 
                className="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-20 transition-opacity duration-300 pointer-events-none"
                style={{background: `linear-gradient(135deg, ${subject.color}40, transparent)`}}
              ></div>
            </div>
          ))}
        </div>

        {/* Info adicional */}
        <div className="mt-16 text-center">
          <div className="bg-black/30 backdrop-blur-sm rounded-lg p-8 max-w-4xl mx-auto border border-purple-500/30">
            <h3 className="text-2xl font-bold mb-4 text-gold-400">
              📜 Reglas del Portal del Despertar
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-left">
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <span className="text-gold-400">✨</span>
                  <span>Diagnóstico adaptativo IRT</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-gold-400">⚔️</span>
                  <span>10 preguntas por materia</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-gold-400">🎯</span>
                  <span>Dificultad se adapta a tu nivel</span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <span className="text-gold-400">🏆</span>
                  <span>Rango E a S según desempeño</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-gold-400">📊</span>
                  <span>Análisis de fortalezas y debilidades</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-gold-400">🔓</span>
                  <span>Desbloquea Arena de Práctica</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Status Message */}
        <div className="mt-16">
          {error ? (
            <div className="text-center bg-red-900/50 rounded-lg p-6 border border-red-500">
              <h2 className="text-red-400 font-bold text-xl mb-2">
                ⚠️ MODO OFFLINE ACTIVADO
              </h2>
              <p className="text-red-300">
                {error}
              </p>
              <p className="text-red-200 text-sm mt-2">
                Ejecutándose con datos básicos de respaldo
              </p>
            </div>
          ) : (
            <div className="text-center bg-green-900/50 rounded-lg p-6 border border-green-500">
              <h2 className="text-green-400 font-bold text-xl mb-2">
                ✅ ¡PORTAL DEL DESPERTAR CONECTADO!
              </h2>
              <p className="text-green-300">
                {subjects.length} materias cargadas con {subjects.reduce((total, subject) => total + subject.questions, 0)} preguntas totales.
              </p>
              <p className="text-green-200 text-sm mt-2">
                🚀 Sistema inteligente conectado con base de datos real
              </p>
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="mt-8 text-center">
          <button
            onClick={handleReturnToHub}
            className="px-8 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg font-bold transition-colors"
          >
            ← Volver al Hub Central
          </button>
        </div>
      </div>
    </div>
  );
}