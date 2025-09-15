'use client';

import React, { ReactNode } from 'react';
import { cn } from '../../lib/utils';

interface MobileContainerProps {
  children: ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  safeArea?: boolean;
  scrollable?: boolean;
}

const MobileContainer: React.FC<MobileContainerProps> = ({
  children,
  className,
  padding = 'md',
  maxWidth = 'xl',
  safeArea = false,
  scrollable = false,
}) => {
  const baseClasses = ['w-full mx-auto'];
  
  const paddingClasses = {
    none: '',
    sm: 'px-4 py-2 mobile:px-3 mobile:py-2',
    md: 'px-6 py-4 mobile:px-4 mobile:py-3',
    lg: 'px-8 py-6 mobile:px-5 mobile:py-4',
  };

  const maxWidthClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-6xl',
    full: 'max-w-full',
  };

  const safeAreaClasses = safeArea ? 'mobile-viewport-fit' : '';
  const scrollClasses = scrollable ? 'mobile-scroll overflow-y-auto' : '';

  const combinedClasses = cn(
    ...baseClasses,
    paddingClasses[padding],
    maxWidthClasses[maxWidth],
    safeAreaClasses,
    scrollClasses,
    className
  );

  return (
    <div className={combinedClasses}>
      {children}
    </div>
  );
};

export default MobileContainer;