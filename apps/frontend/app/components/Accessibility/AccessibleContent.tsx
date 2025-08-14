'use client';

import React, { useEffect, useRef } from 'react';
import TTSButton from '../ui/TTSButton';
import { cn } from '@/lib/utils';
import { Eye, EyeOff, Type, Minus, Plus } from 'lucide-react';

interface AccessibleContentProps {
  children: React.ReactNode;
  className?: string;
  enableTTS?: boolean;
  enableFontSize?: boolean;
  enableHighContrast?: boolean;
  ttsText?: string;
  ariaLabel?: string;
  role?: string;
}

export default function AccessibleContent({
  children,
  className,
  enableTTS = true,
  enableFontSize = true,
  enableHighContrast = true,
  ttsText,
  ariaLabel,
  role = 'article'
}: AccessibleContentProps) {
  const [fontSize, setFontSize] = React.useState(100);
  const [highContrast, setHighContrast] = React.useState(false);
  const contentRef = useRef<HTMLDivElement>(null);
  
  // Extract text content for TTS if not provided
  const getTextContent = () => {
    if (ttsText) return ttsText;
    if (contentRef.current) {
      return contentRef.current.innerText || contentRef.current.textContent || '';
    }
    return '';
  };
  
  // Apply font size
  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.style.fontSize = `${fontSize}%`;
    }
  }, [fontSize]);
  
  const increaseFontSize = () => {
    setFontSize(prev => Math.min(prev + 10, 150));
  };
  
  const decreaseFontSize = () => {
    setFontSize(prev => Math.max(prev - 10, 80));
  };
  
  const resetFontSize = () => {
    setFontSize(100);
  };
  
  const toggleHighContrast = () => {
    setHighContrast(prev => !prev);
  };
  
  return (
    <div className={cn('relative', className)}>
      {/* Accessibility Controls */}
      <div className="flex items-center gap-2 mb-4 p-3 bg-gray-800/50 rounded-lg">
        {enableTTS && (
          <TTSButton
            text={getTextContent()}
            variant="ghost"
            size="md"
            showLabel
          />
        )}
        
        {enableFontSize && (
          <div className="flex items-center gap-1 ml-auto">
            <button
              onClick={decreaseFontSize}
              className="p-2 bg-gray-700 hover:bg-gray-600 text-white rounded 
                transition-all focus:outline-none focus:ring-2 focus:ring-purple-500"
              aria-label="Disminuir tamaño de fuente"
            >
              <Minus className="w-4 h-4" />
            </button>
            
            <button
              onClick={resetFontSize}
              className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded 
                transition-all focus:outline-none focus:ring-2 focus:ring-purple-500
                text-sm font-semibold"
              aria-label="Restablecer tamaño de fuente"
            >
              {fontSize}%
            </button>
            
            <button
              onClick={increaseFontSize}
              className="p-2 bg-gray-700 hover:bg-gray-600 text-white rounded 
                transition-all focus:outline-none focus:ring-2 focus:ring-purple-500"
              aria-label="Aumentar tamaño de fuente"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
        )}
        
        {enableHighContrast && (
          <button
            onClick={toggleHighContrast}
            className={cn(
              'p-2 rounded transition-all ml-2',
              'focus:outline-none focus:ring-2 focus:ring-purple-500',
              highContrast
                ? 'bg-white text-black'
                : 'bg-gray-700 hover:bg-gray-600 text-white'
            )}
            aria-label={highContrast ? 'Desactivar alto contraste' : 'Activar alto contraste'}
            aria-pressed={highContrast}
          >
            {highContrast ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        )}
      </div>
      
      {/* Content */}
      <div
        ref={contentRef}
        role={role}
        aria-label={ariaLabel}
        className={cn(
          'transition-all duration-300',
          highContrast && 'high-contrast'
        )}
      >
        {children}
      </div>
      
      {/* High Contrast Styles */}
      <style jsx>{`
        .high-contrast {
          background-color: white !important;
          color: black !important;
          font-weight: 600;
        }
        
        .high-contrast * {
          background-color: white !important;
          color: black !important;
          border-color: black !important;
        }
        
        .high-contrast a {
          color: #0000FF !important;
          text-decoration: underline !important;
        }
        
        .high-contrast button {
          background-color: black !important;
          color: white !important;
          border: 2px solid black !important;
        }
        
        .high-contrast button:hover {
          background-color: #333 !important;
        }
      `}</style>
    </div>
  );
}