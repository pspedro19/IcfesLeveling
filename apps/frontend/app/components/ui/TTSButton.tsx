'use client';

import React from 'react';
import { Volume2, VolumeX, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTextToSpeech } from '@/hooks/useTextToSpeech';

interface TTSButtonProps {
  text: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  position?: 'inline' | 'absolute';
  variant?: 'default' | 'ghost' | 'primary';
  lang?: string;
  rate?: number;
  showLabel?: boolean;
}

export default function TTSButton({
  text,
  className,
  size = 'sm',
  position = 'inline',
  variant = 'default',
  lang = 'es-ES',
  rate = 1.0,
  showLabel = false
}: TTSButtonProps) {
  const { speak, stop, isSpeaking, isSupported } = useTextToSpeech();
  
  if (!isSupported) return null;
  
  const handleClick = () => {
    if (isSpeaking) {
      stop();
    } else {
      speak(text, { lang, rate });
    }
  };
  
  const sizeStyles = {
    sm: 'p-1.5',
    md: 'p-2',
    lg: 'p-3'
  };
  
  const iconSizes = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6'
  };
  
  const variantStyles = {
    default: 'bg-gray-700 hover:bg-gray-600 text-white',
    ghost: 'bg-transparent hover:bg-gray-800/50 text-gray-400 hover:text-white',
    primary: 'bg-purple-600 hover:bg-purple-700 text-white'
  };
  
  const positionStyles = {
    inline: '',
    absolute: 'absolute top-2 right-2'
  };
  
  return (
    <button
      onClick={handleClick}
      className={cn(
        'rounded-lg transition-all flex items-center gap-2',
        'focus:outline-none focus:ring-2 focus:ring-purple-500',
        sizeStyles[size],
        variantStyles[variant],
        positionStyles[position],
        className
      )}
      title={isSpeaking ? 'Detener lectura' : 'Leer en voz alta'}
      aria-label={isSpeaking ? 'Detener lectura' : 'Leer en voz alta'}
    >
      {isSpeaking ? (
        <>
          <VolumeX className={iconSizes[size]} />
          {showLabel && <span className="text-sm">Detener</span>}
        </>
      ) : (
        <>
          <Volume2 className={iconSizes[size]} />
          {showLabel && <span className="text-sm">Leer</span>}
        </>
      )}
    </button>
  );
}