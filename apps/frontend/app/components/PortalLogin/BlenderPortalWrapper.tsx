'use client';

import React, { memo } from 'react';
import dynamic from 'next/dynamic';

// Dynamically import BlenderPortal with no SSR
const BlenderPortal = dynamic(
  () => import('./BlenderPortal'),
  { 
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-400"></div>
      </div>
    )
  }
);

interface BlenderPortalWrapperProps {
  portalVersion?: 'portal' | 'portal2';
  isTyping?: boolean;
  loginError?: boolean;
  loginSuccess?: boolean;
}

// Memoize the component to prevent unnecessary re-renders
const BlenderPortalWrapper = memo(function BlenderPortalWrapper({
  portalVersion = 'portal2',
  isTyping = false,
  loginError = false,
  loginSuccess = false
}: BlenderPortalWrapperProps) {
  return (
    <BlenderPortal
      portalVersion={portalVersion}
      isTyping={isTyping}
      loginError={loginError}
      loginSuccess={loginSuccess}
    />
  );
});

export default BlenderPortalWrapper;