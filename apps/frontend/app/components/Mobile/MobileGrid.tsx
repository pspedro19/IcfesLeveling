'use client';

import React, { ReactNode } from 'react';
import { cn } from '../../lib/utils';

interface MobileGridProps {
  children: ReactNode;
  columns?: {
    default?: number;
    mobile?: number;
    tablet?: number;
    desktop?: number;
  };
  gap?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  adaptive?: boolean;
}

const MobileGrid: React.FC<MobileGridProps> = ({
  children,
  columns = { mobile: 1, tablet: 2, desktop: 3 },
  gap = 'md',
  className,
  adaptive = true,
}) => {
  const baseClasses = ['grid'];
  
  // Gap classes for different screen sizes
  const gapClasses = {
    sm: 'gap-2 mobile:gap-1',
    md: 'gap-4 mobile:gap-3',
    lg: 'gap-6 mobile:gap-4',
    xl: 'gap-8 mobile:gap-5',
  };

  // Column classes for different breakpoints
  const getColumnClasses = () => {
    const classes: string[] = [];
    
    // Default columns
    if (columns.default) {
      classes.push(`grid-cols-${columns.default}`);
    }
    
    // Mobile columns (applied by default due to mobile-first)
    if (columns.mobile) {
      classes.push(`grid-cols-${columns.mobile}`);
    }
    
    // Tablet columns
    if (columns.tablet) {
      classes.push(`md:grid-cols-${columns.tablet}`);
    }
    
    // Desktop columns
    if (columns.desktop) {
      classes.push(`lg:grid-cols-${columns.desktop}`);
    }

    return classes;
  };

  // Adaptive classes for better mobile experience
  const adaptiveClasses = adaptive ? [
    'mobile:space-y-2', // Add spacing on mobile for stacked layout
    'mobile:grid-cols-1', // Force single column on very small screens
  ] : [];

  const combinedClasses = cn(
    ...baseClasses,
    ...getColumnClasses(),
    gapClasses[gap],
    ...adaptiveClasses,
    className
  );

  return (
    <div className={combinedClasses}>
      {children}
    </div>
  );
};

export default MobileGrid;