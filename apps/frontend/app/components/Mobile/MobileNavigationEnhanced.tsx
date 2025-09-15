'use client';

import React, { useState, useEffect } from 'react';
import { cn } from '../../lib/utils';
import { useMediaQuery } from '../../hooks/useMediaQuery';

interface NavigationItem {
  id: string;
  label: string;
  icon: string;
  href: string;
  badge?: number;
  active?: boolean;
}

interface MobileNavigationEnhancedProps {
  items?: NavigationItem[];
  position?: 'bottom' | 'top';
  variant?: 'default' | 'gaming' | 'minimal';
  safeArea?: boolean;
  hapticFeedback?: boolean;
}

const defaultItems: NavigationItem[] = [
  { id: 'home', label: 'Home', icon: '🏠', href: '/' },
  { id: 'diagnostic', label: 'Test', icon: '🎯', href: '/mobile-diagnostic' },
  { id: 'progress', label: 'Progress', icon: '📊', href: '/progress' },
  { id: 'study', label: 'Study', icon: '📚', href: '/study' },
  { id: 'profile', label: 'Profile', icon: '👤', href: '/profile' },
];

const MobileNavigationEnhanced: React.FC<MobileNavigationEnhancedProps> = ({
  items = defaultItems,
  position = 'bottom',
  variant = 'gaming',
  safeArea = true,
  hapticFeedback = true,
}) => {
  const [activeItem, setActiveItem] = useState<string>('home');
  const [isVisible, setIsVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);
  
  const isMobile = useMediaQuery('(max-width: 767px)');
  
  // Auto-hide navigation on scroll (mobile only)
  useEffect(() => {
    if (!isMobile) return;
    
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      
      if (currentScrollY > lastScrollY && currentScrollY > 100) {
        // Scrolling down
        setIsVisible(false);
      } else {
        // Scrolling up
        setIsVisible(true);
      }
      
      setLastScrollY(currentScrollY);
    };
    
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [lastScrollY, isMobile]);

  const handleItemClick = (item: NavigationItem) => {
    if (hapticFeedback && navigator.vibrate) {
      navigator.vibrate(25); // Light haptic feedback
    }
    
    setActiveItem(item.id);
    
    // Navigate to the item's href
    if (item.href.startsWith('/')) {
      window.location.href = item.href;
    }
  };

  const getVariantClasses = () => {
    switch (variant) {
      case 'gaming':
        return {
          container: [
            'bg-gradient-to-r from-black/90 via-purple-900/80 to-black/90',
            'backdrop-blur-xl border-t border-purple-500/30',
            'shadow-[0_-10px_30px_rgba(147,51,234,0.4)]'
          ].join(' '),
          item: 'hover:bg-purple-600/20',
          activeItem: 'bg-purple-600/30 text-game-neonGold shadow-[0_0_15px_rgba(255,215,0,0.5)]',
        };
      case 'minimal':
        return {
          container: 'bg-white/95 backdrop-blur-md border-t border-gray-200 shadow-lg',
          item: 'hover:bg-gray-100',
          activeItem: 'bg-blue-100 text-blue-600',
        };
      default:
        return {
          container: 'bg-gray-900/95 backdrop-blur-md border-t border-gray-700 shadow-2xl',
          item: 'hover:bg-gray-700/50',
          activeItem: 'bg-blue-600/20 text-blue-400',
        };
    }
  };

  const variantClasses = getVariantClasses();

  const containerClasses = cn(
    'fixed left-0 right-0 z-50 transition-transform duration-300',
    position === 'bottom' ? 'bottom-0' : 'top-0',
    safeArea && position === 'bottom' ? 'pb-safe-area-inset-bottom' : '',
    safeArea && position === 'top' ? 'pt-safe-area-inset-top' : '',
    variantClasses.container,
    isVisible ? 'translate-y-0' : position === 'bottom' ? 'translate-y-full' : '-translate-y-full'
  );

  // Don't render on desktop unless explicitly needed
  if (!isMobile) {
    return null;
  }

  return (
    <nav className={containerClasses}>
      <div className="flex items-center justify-around px-2 py-2 min-h-[60px]">
        {items.map((item) => {
          const isActive = activeItem === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => handleItemClick(item)}
              className={cn(
                'flex flex-col items-center justify-center',
                'min-w-[60px] min-h-[48px] px-2 py-1',
                'rounded-lg transition-all duration-200',
                'touch-manipulation active:scale-95',
                'focus:outline-none focus:ring-2 focus:ring-purple-500/50',
                variantClasses.item,
                isActive ? variantClasses.activeItem : 'text-gray-400'
              )}
              aria-label={item.label}
              role="tab"
              aria-selected={isActive}
            >
              <div className="relative">
                <span className={cn(
                  'text-xl mb-1 block transition-transform duration-200',
                  isActive ? 'scale-110' : 'scale-100'
                )}>
                  {item.icon}
                </span>
                
                {item.badge && item.badge > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1">
                    {item.badge > 99 ? '99+' : item.badge}
                  </span>
                )}
              </div>
              
              <span className={cn(
                'text-xs font-medium truncate max-w-full',
                'transition-colors duration-200',
                isActive ? 'font-semibold' : 'font-normal'
              )}>
                {item.label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};

export default MobileNavigationEnhanced;