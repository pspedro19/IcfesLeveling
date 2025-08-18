'use client';

import React from 'react';
import dynamic from 'next/dynamic';

// Importar dinámicamente los componentes para evitar problemas de compilación
const HybridStudyPlanUX = dynamic(() => import('./HybridStudyPlanUX'), {
  loading: () => (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
      <div className="text-center text-white">
        <div className="animate-spin w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full mx-auto mb-4"></div>
        <p className="text-lg font-medium">Cargando plan de estudio...</p>
      </div>
    </div>
  ),
  ssr: false
});

const CourseraGradeStudyPlan = dynamic(() => import('./CourseraGradeStudyPlan'), {
  loading: () => (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-black flex items-center justify-center">
      <div className="text-center text-white">
        <div className="animate-spin w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full mx-auto mb-4"></div>
        <p className="text-lg font-medium">Cargando plan de estudio...</p>
      </div>
    </div>
  ),
  ssr: false
});

// ===== TIPOS E INTERFACES =====
interface StudyPlanRouterProps {
  userId: string;
  subject: string;
  diagnosticScore: number;
  weakTopics: string[];
  strongTopics: string[];
  
  // Props específicos para Coursera (legacy)
  onModuleStart?: (moduleId: string) => void;
  onVideoComplete?: (videoId: string, xp: number) => void;
  
  // Props específicos para Hybrid (nuevo)
  onUnitStart?: (unitId: string) => void;
  onTopicStart?: (topicId: string, unitId: string) => void;
  onProgressUpdate?: (unitId: string, progress: number) => void;
  
  // Configuración del router
  useHybridSystem?: boolean; // Por defecto true para usar el nuevo sistema
  fallbackToCoursera?: boolean; // Si hay error, usar Coursera como fallback
}

// ===== COMPONENTE PRINCIPAL =====
const StudyPlanRouter: React.FC<StudyPlanRouterProps> = ({
  userId,
  subject,
  diagnosticScore,
  weakTopics,
  strongTopics,
  onModuleStart,
  onVideoComplete,
  onUnitStart,
  onTopicStart,
  onProgressUpdate,
  useHybridSystem = true, // Por defecto usar el nuevo sistema
  fallbackToCoursera = true
}) => {
  
  // Estado para manejo de errores
  const [hasError, setHasError] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState<string>('');

  // Error boundary manual
  React.useEffect(() => {
    const handleError = (error: ErrorEvent) => {
      console.error('StudyPlan Error:', error);
      if (fallbackToCoursera && useHybridSystem) {
        setHasError(true);
        setErrorMessage('Usando sistema de respaldo...');
      }
    };

    window.addEventListener('error', handleError);
    return () => window.removeEventListener('error', handleError);
  }, [fallbackToCoursera, useHybridSystem]);

  // Determinar qué componente usar
  const shouldUseHybrid = useHybridSystem && !hasError;

  if (shouldUseHybrid) {
    return (
      <HybridStudyPlanUX
        userId={userId}
        subject={subject}
        diagnosticScore={diagnosticScore}
        weakTopics={weakTopics}
        strongTopics={strongTopics}
        onUnitStart={onUnitStart}
        onTopicStart={onTopicStart}
        onProgressUpdate={onProgressUpdate}
      />
    );
  }

  // Fallback al sistema Coursera
  return (
    <div>
      {hasError && (
        <div className="bg-yellow-500/20 border border-yellow-400/30 text-yellow-300 p-4 rounded-lg mb-4 mx-4">
          <p className="text-sm">
            ⚠️ {errorMessage} Usando sistema de respaldo compatible.
          </p>
        </div>
      )}
      
      <CourseraGradeStudyPlan
        userId={userId}
        subject={subject}
        diagnosticScore={diagnosticScore}
        weakTopics={weakTopics}
        strongTopics={strongTopics}
        onModuleStart={onModuleStart || ((moduleId) => console.log('Module started:', moduleId))}
        onVideoComplete={onVideoComplete || ((videoId, xp) => console.log('Video completed:', videoId, 'XP:', xp))}
      />
    </div>
  );
};

export default StudyPlanRouter;
