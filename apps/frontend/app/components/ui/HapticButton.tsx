'use client';

import React from 'react';
import { motion, MotionProps } from 'framer-motion';
import { useHapticFeedback } from '@/hooks/useHapticFeedback';
import { cn } from '@/lib/utils';

interface HapticButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  hapticStyle?: 'light' | 'medium' | 'heavy';
  hapticPattern?: 'tap' | 'doubleTap' | 'success' | 'error' | 'epic';
  motionProps?: MotionProps;
  fullWidth?: boolean;
}

export default function HapticButton({
  children,
  className,
  variant = 'primary',
  size = 'md',
  hapticStyle = 'medium',
  hapticPattern = 'tap',
  motionProps,
  fullWidth = false,
  onClick,
  disabled,
  ...props
}: HapticButtonProps) {
  const haptics = useHapticFeedback();
  
  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (disabled) return;
    
    // Trigger haptic feedback
    if (hapticPattern === 'tap') {
      haptics.impact(hapticStyle);
    } else {
      haptics.vibratePattern(hapticPattern);
    }
    
    // Call original onClick
    onClick?.(e);
  };
  
  const baseStyles = cn(
    'relative font-semibold transition-all duration-200',
    'focus:outline-none focus:ring-2 focus:ring-offset-2',
    'disabled:opacity-50 disabled:cursor-not-allowed',
    'transform active:scale-95',
    fullWidth && 'w-full'
  );
  
  const variantStyles = {
    primary: cn(
      'bg-gradient-to-r from-purple-600 to-purple-700',
      'hover:from-purple-700 hover:to-purple-800',
      'text-white shadow-lg hover:shadow-xl',
      'focus:ring-purple-500'
    ),
    secondary: cn(
      'bg-gray-700 hover:bg-gray-600',
      'text-white shadow-md hover:shadow-lg',
      'focus:ring-gray-500'
    ),
    danger: cn(
      'bg-gradient-to-r from-red-600 to-red-700',
      'hover:from-red-700 hover:to-red-800',
      'text-white shadow-lg hover:shadow-xl',
      'focus:ring-red-500'
    ),
    success: cn(
      'bg-gradient-to-r from-green-600 to-green-700',
      'hover:from-green-700 hover:to-green-800',
      'text-white shadow-lg hover:shadow-xl',
      'focus:ring-green-500'
    ),
    ghost: cn(
      'bg-transparent hover:bg-gray-800/50',
      'text-gray-300 hover:text-white',
      'focus:ring-gray-500'
    )
  };
  
  const sizeStyles = {
    sm: 'px-3 py-1.5 text-sm rounded-lg',
    md: 'px-5 py-2.5 text-base rounded-lg',
    lg: 'px-8 py-4 text-lg rounded-xl'
  };
  
  return (
    <motion.button
      className={cn(
        baseStyles,
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      onClick={handleClick}
      disabled={disabled}
      whileHover={!disabled ? { scale: 1.05 } : {}}
      whileTap={!disabled ? { scale: 0.95 } : {}}
      {...motionProps}
      {...props}
    >
      {/* Ripple Effect on Click */}
      <motion.span
        className="absolute inset-0 rounded-lg"
        initial={{ opacity: 0 }}
        whileTap={!disabled ? {
          opacity: [0, 0.2, 0],
          scale: [0.8, 1.2, 1.2],
        } : {}}
        transition={{ duration: 0.6 }}
        style={{
          background: 'radial-gradient(circle, rgba(255,255,255,0.3) 0%, transparent 70%)',
        }}
      />
      
      {/* Button Content */}
      <span className="relative z-10 flex items-center justify-center gap-2">
        {children}
      </span>
    </motion.button>
  );
}