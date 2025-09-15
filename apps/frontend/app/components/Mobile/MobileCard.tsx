'use client';

import React, { ReactNode } from 'react';
import { cn } from '../../lib/utils';

interface MobileCardProps {
  children: ReactNode;
  title?: string;
  subtitle?: string;
  icon?: ReactNode;
  onClick?: () => void;
  className?: string;
  variant?: 'default' | 'gaming' | 'elevated';
  size?: 'compact' | 'default' | 'large';
  interactive?: boolean;
}

const MobileCard: React.FC<MobileCardProps> = ({
  children,
  title,
  subtitle,
  icon,
  onClick,
  className,
  variant = 'default',
  size = 'default',
  interactive = false,
}) => {
  const baseClasses = [
    'rounded-lg overflow-hidden',
    'transition-all duration-300 ease-in-out',
    'touch-manipulation',
  ];

  const sizeClasses = {
    compact: 'p-4 min-h-[120px]',
    default: 'p-6 min-h-[160px]',
    large: 'p-8 min-h-[200px]',
  };

  const variantClasses = {
    default: [
      'bg-white/10 backdrop-blur-sm',
      'border border-white/20',
      'text-white',
    ].join(' '),
    gaming: [
      'bg-gradient-to-br from-black/40 via-purple-900/20 to-black/40',
      'backdrop-blur-sm border border-purple-500/30',
      'text-white shadow-[0_0_20px_rgba(147,51,234,0.3)]',
    ].join(' '),
    elevated: [
      'bg-gradient-to-br from-gray-900/80 to-gray-800/80',
      'backdrop-blur-md border border-gray-700/50',
      'text-white shadow-2xl',
    ].join(' '),
  };

  const interactiveClasses = interactive || onClick ? [
    'cursor-pointer transform hover:scale-[1.02]',
    'active:scale-[0.98]',
    'hover:shadow-xl',
    variant === 'gaming' ? 'hover:shadow-[0_0_30px_rgba(255,215,0,0.4)]' : '',
    'focus:outline-none focus:ring-2 focus:ring-purple-500/50',
  ].join(' ') : '';

  const combinedClasses = cn(
    ...baseClasses,
    sizeClasses[size],
    variantClasses[variant],
    interactiveClasses,
    className
  );

  const CardContent = () => (
    <>
      {(title || subtitle || icon) && (
        <div className="flex items-start gap-4 mb-4">
          {icon && (
            <div className="flex-shrink-0 w-12 h-12 rounded-full bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center text-xl">
              {icon}
            </div>
          )}
          <div className="flex-1 min-w-0">
            {title && (
              <h3 className="text-lg font-semibold text-white mb-1 truncate mobile:text-base">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-sm text-gray-300 truncate mobile:text-xs">
                {subtitle}
              </p>
            )}
          </div>
        </div>
      )}
      <div className="flex-1">
        {children}
      </div>
    </>
  );

  if (onClick) {
    return (
      <button
        className={combinedClasses}
        onClick={onClick}
        type="button"
        role="button"
        tabIndex={0}
      >
        <CardContent />
      </button>
    );
  }

  return (
    <div 
      className={combinedClasses}
      role={interactive ? 'button' : undefined}
      tabIndex={interactive ? 0 : undefined}
    >
      <CardContent />
    </div>
  );
};

export default MobileCard;