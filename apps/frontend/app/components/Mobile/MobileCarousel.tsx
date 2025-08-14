'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, useMotionValue, useTransform, PanInfo } from 'framer-motion';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useMediaQuery } from '@/hooks/useMediaQuery';

interface CarouselItem {
  id: string;
  content: React.ReactNode;
}

interface MobileCarouselProps {
  items: CarouselItem[];
  itemWidth?: number;
  gap?: number;
  showIndicators?: boolean;
  autoPlay?: boolean;
  autoPlayInterval?: number;
  onSlideChange?: (index: number) => void;
}

export default function MobileCarousel({
  items,
  itemWidth = 280,
  gap = 16,
  showIndicators = true,
  autoPlay = false,
  autoPlayInterval = 5000,
  onSlideChange
}: MobileCarouselProps) {
  const isMobile = useMediaQuery('(max-width: 768px)');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [containerWidth, setContainerWidth] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const x = useMotionValue(0);
  
  // Calculate dimensions
  useEffect(() => {
    if (containerRef.current) {
      setContainerWidth(containerRef.current.offsetWidth);
    }
    
    const handleResize = () => {
      if (containerRef.current) {
        setContainerWidth(containerRef.current.offsetWidth);
      }
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  const slideWidth = isMobile ? containerWidth : itemWidth + gap;
  const maxIndex = items.length - 1;
  
  // Auto-play functionality
  useEffect(() => {
    if (!autoPlay) return;
    
    const interval = setInterval(() => {
      handleNext();
    }, autoPlayInterval);
    
    return () => clearInterval(interval);
  }, [autoPlay, autoPlayInterval, currentIndex]);
  
  const handleDragEnd = (event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    const threshold = slideWidth * 0.2;
    
    if (info.offset.x > threshold && currentIndex > 0) {
      handlePrevious();
    } else if (info.offset.x < -threshold && currentIndex < maxIndex) {
      handleNext();
    } else {
      // Snap back to current position
      x.set(-currentIndex * slideWidth);
    }
  };
  
  const handleNext = () => {
    if (currentIndex < maxIndex) {
      const newIndex = currentIndex + 1;
      setCurrentIndex(newIndex);
      x.set(-newIndex * slideWidth);
      onSlideChange?.(newIndex);
    }
  };
  
  const handlePrevious = () => {
    if (currentIndex > 0) {
      const newIndex = currentIndex - 1;
      setCurrentIndex(newIndex);
      x.set(-newIndex * slideWidth);
      onSlideChange?.(newIndex);
    }
  };
  
  const goToSlide = (index: number) => {
    setCurrentIndex(index);
    x.set(-index * slideWidth);
    onSlideChange?.(index);
  };
  
  return (
    <div className="relative w-full">
      {/* Carousel Container */}
      <div
        ref={containerRef}
        className="relative overflow-hidden"
        style={{ touchAction: 'pan-y' }}
      >
        <motion.div
          className="flex"
          style={{ x, gap: `${gap}px` }}
          drag="x"
          dragConstraints={{
            left: -((items.length - 1) * slideWidth),
            right: 0
          }}
          dragElastic={0.2}
          onDragEnd={handleDragEnd}
          animate={{ x: -currentIndex * slideWidth }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        >
          {items.map((item, index) => (
            <motion.div
              key={item.id}
              className="flex-shrink-0"
              style={{
                width: isMobile ? `${containerWidth}px` : `${itemWidth}px`,
                paddingLeft: isMobile ? '16px' : '0',
                paddingRight: isMobile ? '16px' : '0'
              }}
            >
              {item.content}
            </motion.div>
          ))}
        </motion.div>
      </div>
      
      {/* Navigation Buttons (Desktop) */}
      {!isMobile && (
        <>
          <button
            onClick={handlePrevious}
            disabled={currentIndex === 0}
            className={`absolute left-2 top-1/2 -translate-y-1/2 bg-gray-900/80 
              text-white p-2 rounded-full transition-all ${
              currentIndex === 0 
                ? 'opacity-50 cursor-not-allowed' 
                : 'hover:bg-gray-800'
            }`}
          >
            <ChevronLeft className="w-6 h-6" />
          </button>
          
          <button
            onClick={handleNext}
            disabled={currentIndex === maxIndex}
            className={`absolute right-2 top-1/2 -translate-y-1/2 bg-gray-900/80 
              text-white p-2 rounded-full transition-all ${
              currentIndex === maxIndex 
                ? 'opacity-50 cursor-not-allowed' 
                : 'hover:bg-gray-800'
            }`}
          >
            <ChevronRight className="w-6 h-6" />
          </button>
        </>
      )}
      
      {/* Indicators */}
      {showIndicators && (
        <div className="flex justify-center gap-2 mt-4">
          {items.map((_, index) => (
            <button
              key={index}
              onClick={() => goToSlide(index)}
              className={`transition-all ${
                index === currentIndex
                  ? 'w-8 h-2 bg-purple-500 rounded-full'
                  : 'w-2 h-2 bg-gray-600 rounded-full hover:bg-gray-500'
              }`}
            />
          ))}
        </div>
      )}
      
      {/* Mobile Swipe Hint */}
      {isMobile && items.length > 1 && (
        <motion.div
          className="absolute bottom-20 left-1/2 -translate-x-1/2 
            bg-purple-600/20 backdrop-blur-sm px-4 py-2 rounded-full
            text-purple-300 text-sm pointer-events-none"
          initial={{ opacity: 1 }}
          animate={{ opacity: 0 }}
          transition={{ delay: 3, duration: 1 }}
        >
          <motion.div
            animate={{ x: [-10, 10, -10] }}
            transition={{ repeat: 2, duration: 1 }}
            className="flex items-center gap-2"
          >
            <ChevronLeft className="w-4 h-4" />
            Desliza para ver más
            <ChevronRight className="w-4 h-4" />
          </motion.div>
        </motion.div>
      )}
    </div>
  );
}