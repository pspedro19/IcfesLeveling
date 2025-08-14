'use client';

import React from 'react';
import ICFESModularSelector from '../components/ICFESModularSelector';
import { useRouter } from 'next/navigation';

export default function ICFESSelectorPage() {
  const router = useRouter();
  
  const handleModuleSelection = (selectedModules: string[]) => {
    console.log('Módulos seleccionados:', selectedModules);
    
    // Guardar en localStorage o enviar al backend
    localStorage.setItem('selectedICFESModules', JSON.stringify(selectedModules));
    
    // Redirigir al siguiente paso del onboarding o al dashboard
    router.push('/onboarding?step=personality');
  };
  
  return (
    <ICFESModularSelector
      onComplete={handleModuleSelection}
      minModules={5}
      maxModules={5}
      userLevel={1}
    />
  );
}