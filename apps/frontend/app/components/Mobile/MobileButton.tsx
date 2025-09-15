'use client';

import React, { ReactNode } from 'react';
import { cn } from '../../lib/utils';

interface MobileButtonProps {
  children: ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'warning';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  className?: string;
}

const MobileButton: React.FC<MobileButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  fullWidth = false,
  className,
}) => {
  const baseClasses = [
    'inline-flex items-center justify-center',
    'font-semibold rounded-lg',
    'transition-all duration-200',
    'touch-manipulation tap-highlight-none',
    'focus:outline-none focus:ring-2 focus:ring-offset-2',
    'active:scale-95',
    'select-none',
  ];

  // Minimum touch target size (44px)
  const sizeClasses = {
    sm: 'px-4 py-2 min-h-[44px] text-sm',
    md: 'px-6 py-3 min-h-[48px] text-base',
    lg: 'px-8 py-4 min-h-[52px] text-lg',
  };

  const variantClasses = {
    primary: [
      'bg-gradient-to-r from-purple-600 to-blue-600',
      'hover:from-purple-700 hover:to-blue-700',
      'text-white',
      'focus:ring-purple-500',
      'disabled:from-gray-400 disabled:to-gray-500'
    ].join(' '),
    secondary: [
      'bg-gray-600 hover:bg-gray-700',
      'text-white',
      'focus:ring-gray-500',
      'disabled:bg-gray-400'
    ].join(' '),
    success: [
      'bg-gradient-to-r from-green-600 to-emerald-600',
      'hover:from-green-700 hover:to-emerald-700',
      'text-white',
      'focus:ring-green-500',
      'disabled:from-gray-400 disabled:to-gray-500'
    ].join(' '),
    danger: [
      'bg-gradient-to-r from-red-600 to-rose-600',
      'hover:from-red-700 hover:to-rose-700',
      'text-white',
      'focus:ring-red-500',
      'disabled:from-gray-400 disabled:to-gray-500'
    ].join(' '),
    warning: [
      'bg-gradient-to-r from-yellow-600 to-orange-600',
      'hover:from-yellow-700 hover:to-orange-700',
      'text-white',
      'focus:ring-yellow-500',
      'disabled:from-gray-400 disabled:to-gray-500'
    ].join(' '),
  };

  const disabledClasses = disabled || loading ? 'cursor-not-allowed opacity-60' : 'cursor-pointer';
  const widthClasses = fullWidth ? 'w-full' : '';

  const combinedClasses = cn(
    ...baseClasses,
    sizeClasses[size],
    variantClasses[variant],
    disabledClasses,
    widthClasses,
    className
  );

  return (
    <button
      className={combinedClasses}
      onClick={onClick}
      disabled={disabled || loading}
      type="button"
    >
      {loading && (
        <svg 
          className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" 
          xmlns="http://www.w3.org/2000/svg" 
          fill="none" 
          viewBox="0 0 24 24"
        >
          <circle 
            className="opacity-25" 
            cx="12" 
            cy="12" 
            r="10" 
            stroke="currentColor" 
            strokeWidth="4"
          />
          <path 
            className="opacity-75" 
            fill="currentColor" 
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      {children}
    </button>
  );
};

export default MobileButton;