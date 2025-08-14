'use client';

import React from 'react';
import OnboardingMap from '@/components/OnboardingMap';
import { AudioProvider } from '@/components/PortalLogin/AudioEngine';

export default function OnboardingMapPage() {
  return (
    <AudioProvider>
      <OnboardingMap />
    </AudioProvider>
  );
}