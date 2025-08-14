'use client';

import React from 'react';
import YAMLRenderer from '@/components/YAMLRenderer';
import { QueryProvider } from '@/providers/QueryProvider';
import { AudioProvider } from '@/components/PortalLogin/AudioEngine';
import { useRouter } from 'next/navigation';

export default function YAMLRendererPage() {
  const router = useRouter();
  
  const handleUnitSelect = (unit: any) => {
    console.log('Unit selected:', unit);
    // Navigate to battle or quiz page with unit data
    router.push(`/unit-quiz?unit=${encodeURIComponent(unit.name)}`);
  };
  
  // Mock weakness data for demonstration
  const mockWeaknessData = {
    'algebra': 45,
    'geometry': 60,
    'calculus': 30,
    'statistics': 75
  };
  
  return (
    <QueryProvider>
      <AudioProvider>
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-indigo-900 py-8">
          <div className="container mx-auto px-4">
            <h1 className="text-3xl font-bold text-white text-center mb-8 font-cinzel">
              Sistema de Mazmorras Dinámicas
            </h1>
            
            <YAMLRenderer
              subject="Matemáticas"
              userLevel={15}
              weaknessData={mockWeaknessData}
              onUnitSelect={handleUnitSelect}
            />
          </div>
        </div>
      </AudioProvider>
    </QueryProvider>
  );
}