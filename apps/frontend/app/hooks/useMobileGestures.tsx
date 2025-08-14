import { useEffect, useState, useRef } from 'react';
import { useMediaQuery } from './useMediaQuery';

interface SwipeHandlers {
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  onSwipeUp?: () => void;
  onSwipeDown?: () => void;
  threshold?: number;
  preventDefaultTouchmoveEvent?: boolean;
}

interface TouchPosition {
  x: number;
  y: number;
  time: number;
}

export function useMobileGestures({
  onSwipeLeft,
  onSwipeRight,
  onSwipeUp,
  onSwipeDown,
  threshold = 50,
  preventDefaultTouchmoveEvent = false
}: SwipeHandlers) {
  const isMobile = useMediaQuery('(max-width: 768px)');
  const [isSwipeInProgress, setIsSwipeInProgress] = useState(false);
  const touchStart = useRef<TouchPosition | null>(null);
  const touchEnd = useRef<TouchPosition | null>(null);
  
  useEffect(() => {
    if (!isMobile) return;
    
    const handleTouchStart = (e: TouchEvent) => {
      touchEnd.current = null;
      touchStart.current = {
        x: e.targetTouches[0].clientX,
        y: e.targetTouches[0].clientY,
        time: Date.now()
      };
      setIsSwipeInProgress(true);
    };
    
    const handleTouchMove = (e: TouchEvent) => {
      if (preventDefaultTouchmoveEvent) {
        e.preventDefault();
      }
      
      touchEnd.current = {
        x: e.targetTouches[0].clientX,
        y: e.targetTouches[0].clientY,
        time: Date.now()
      };
    };
    
    const handleTouchEnd = () => {
      if (!touchStart.current || !touchEnd.current) return;
      
      const deltaX = touchStart.current.x - touchEnd.current.x;
      const deltaY = touchStart.current.y - touchEnd.current.y;
      const deltaTime = touchEnd.current.time - touchStart.current.time;
      
      // Calculate velocity
      const velocityX = Math.abs(deltaX) / deltaTime;
      const velocityY = Math.abs(deltaY) / deltaTime;
      
      // Determine if it's a swipe based on distance and velocity
      const isSwipe = Math.abs(deltaX) > threshold || Math.abs(deltaY) > threshold;
      const isFastSwipe = velocityX > 0.5 || velocityY > 0.5;
      
      if (isSwipe || isFastSwipe) {
        if (Math.abs(deltaX) > Math.abs(deltaY)) {
          // Horizontal swipe
          if (deltaX > 0) {
            onSwipeLeft?.();
          } else {
            onSwipeRight?.();
          }
        } else {
          // Vertical swipe
          if (deltaY > 0) {
            onSwipeUp?.();
          } else {
            onSwipeDown?.();
          }
        }
      }
      
      setIsSwipeInProgress(false);
    };
    
    document.addEventListener('touchstart', handleTouchStart);
    document.addEventListener('touchmove', handleTouchMove);
    document.addEventListener('touchend', handleTouchEnd);
    
    return () => {
      document.removeEventListener('touchstart', handleTouchStart);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleTouchEnd);
    };
  }, [isMobile, onSwipeLeft, onSwipeRight, onSwipeUp, onSwipeDown, threshold, preventDefaultTouchmoveEvent]);
  
  return { isSwipeInProgress, isMobile };
}

// Hook for pinch zoom gestures
export function usePinchZoom(
  elementRef: React.RefObject<HTMLElement>,
  minScale = 0.5,
  maxScale = 3
) {
  const [scale, setScale] = useState(1);
  const [isZooming, setIsZooming] = useState(false);
  const initialDistance = useRef<number | null>(null);
  
  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;
    
    const handleTouchStart = (e: TouchEvent) => {
      if (e.touches.length === 2) {
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        
        initialDistance.current = Math.hypot(
          touch2.clientX - touch1.clientX,
          touch2.clientY - touch1.clientY
        );
        
        setIsZooming(true);
      }
    };
    
    const handleTouchMove = (e: TouchEvent) => {
      if (e.touches.length === 2 && initialDistance.current) {
        e.preventDefault();
        
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        
        const currentDistance = Math.hypot(
          touch2.clientX - touch1.clientX,
          touch2.clientY - touch1.clientY
        );
        
        const delta = currentDistance / initialDistance.current;
        const newScale = Math.max(minScale, Math.min(maxScale, scale * delta));
        
        setScale(newScale);
        element.style.transform = `scale(${newScale})`;
      }
    };
    
    const handleTouchEnd = () => {
      setIsZooming(false);
      initialDistance.current = null;
    };
    
    element.addEventListener('touchstart', handleTouchStart, { passive: false });
    element.addEventListener('touchmove', handleTouchMove, { passive: false });
    element.addEventListener('touchend', handleTouchEnd);
    
    return () => {
      element.removeEventListener('touchstart', handleTouchStart);
      element.removeEventListener('touchmove', handleTouchMove);
      element.removeEventListener('touchend', handleTouchEnd);
    };
  }, [elementRef, scale, minScale, maxScale]);
  
  return { scale, isZooming, resetScale: () => setScale(1) };
}

// Hook for double tap
export function useDoubleTap(
  callback: () => void,
  delay = 300
) {
  const [lastTap, setLastTap] = useState(0);
  
  const handleTap = () => {
    const now = Date.now();
    
    if (now - lastTap < delay) {
      callback();
      setLastTap(0);
    } else {
      setLastTap(now);
    }
  };
  
  return handleTap;
}