'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Home, 
  Sword, 
  Trophy, 
  Users, 
  User,
  Menu,
  X,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { useRouter, usePathname } from 'next/navigation';
import { useMobileGestures } from '@/hooks/useMobileGestures';
import { useAudio } from '../PortalLogin/AudioEngine';

interface NavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  path: string;
  color: string;
}

const NAV_ITEMS: NavItem[] = [
  {
    id: 'home',
    label: 'Inicio',
    icon: <Home className="w-6 h-6" />,
    path: '/',
    color: 'from-purple-500 to-purple-600'
  },
  {
    id: 'battles',
    label: 'Batallas',
    icon: <Sword className="w-6 h-6" />,
    path: '/test',
    color: 'from-red-500 to-red-600'
  },
  {
    id: 'leaderboard',
    label: 'Ranking',
    icon: <Trophy className="w-6 h-6" />,
    path: '/leaderboards',
    color: 'from-yellow-500 to-yellow-600'
  },
  {
    id: 'guilds',
    label: 'Gremios',
    icon: <Users className="w-6 h-6" />,
    path: '/guilds',
    color: 'from-green-500 to-green-600'
  },
  {
    id: 'profile',
    label: 'Perfil',
    icon: <User className="w-6 h-6" />,
    path: '/profile',
    color: 'from-blue-500 to-blue-600'
  }
];

export default function MobileNavigation() {
  const router = useRouter();
  const pathname = usePathname();
  const { playSound } = useAudio();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(
    NAV_ITEMS.findIndex(item => item.path === pathname) || 0
  );
  
  // Swipe gestures
  const { isMobile } = useMobileGestures({
    onSwipeLeft: () => navigateToNext(),
    onSwipeRight: () => navigateToPrevious(),
    threshold: 50
  });
  
  const navigateToNext = () => {
    if (activeIndex < NAV_ITEMS.length - 1) {
      const nextIndex = activeIndex + 1;
      navigateToItem(NAV_ITEMS[nextIndex], nextIndex);
    }
  };
  
  const navigateToPrevious = () => {
    if (activeIndex > 0) {
      const prevIndex = activeIndex - 1;
      navigateToItem(NAV_ITEMS[prevIndex], prevIndex);
    }
  };
  
  const navigateToItem = (item: NavItem, index: number) => {
    playSound('typing_click');
    setActiveIndex(index);
    router.push(item.path);
    setIsMenuOpen(false);
  };
  
  const activeItem = NAV_ITEMS[activeIndex];
  
  if (!isMobile) return null;
  
  return (
    <>
      {/* Top Navigation Bar */}
      <div className="fixed top-0 left-0 right-0 bg-gray-900/95 backdrop-blur-sm 
        border-b border-gray-800 z-40 md:hidden">
        <div className="flex items-center justify-between p-4">
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="text-white hover:text-purple-400 transition-colors"
          >
            {isMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
          
          <h1 className="text-lg font-bold text-white font-cinzel">
            {activeItem.label}
          </h1>
          
          <div className="w-6" /> {/* Spacer for centering */}
        </div>
        
        {/* Swipe Indicator */}
        <div className="px-4 pb-2">
          <div className="flex items-center justify-center gap-2">
            <ChevronLeft className={`w-4 h-4 ${
              activeIndex > 0 ? 'text-purple-400' : 'text-gray-600'
            }`} />
            
            <div className="flex gap-1">
              {NAV_ITEMS.map((_, index) => (
                <div
                  key={index}
                  className={`h-1 rounded-full transition-all ${
                    index === activeIndex 
                      ? 'w-6 bg-purple-500' 
                      : 'w-1 bg-gray-600'
                  }`}
                />
              ))}
            </div>
            
            <ChevronRight className={`w-4 h-4 ${
              activeIndex < NAV_ITEMS.length - 1 ? 'text-purple-400' : 'text-gray-600'
            }`} />
          </div>
          
          <p className="text-xs text-center text-gray-500 mt-1">
            Desliza para navegar
          </p>
        </div>
      </div>
      
      {/* Bottom Tab Bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-gray-900/95 backdrop-blur-sm 
        border-t border-gray-800 z-40 md:hidden">
        <div className="flex justify-around items-center py-2">
          {NAV_ITEMS.map((item, index) => (
            <motion.button
              key={item.id}
              onClick={() => navigateToItem(item, index)}
              className={`flex flex-col items-center justify-center p-2 rounded-lg
                transition-all ${
                index === activeIndex 
                  ? 'text-white' 
                  : 'text-gray-500 hover:text-gray-300'
              }`}
              whileTap={{ scale: 0.9 }}
            >
              <div className={`p-2 rounded-lg ${
                index === activeIndex 
                  ? `bg-gradient-to-r ${item.color}` 
                  : ''
              }`}>
                {item.icon}
              </div>
              
              <span className="text-xs mt-1">
                {item.label}
              </span>
            </motion.button>
          ))}
        </div>
      </div>
      
      {/* Slide Menu */}
      <AnimatePresence>
        {isMenuOpen && (
          <>
            <motion.div
              className="fixed inset-0 bg-black/50 z-40 md:hidden"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsMenuOpen(false)}
            />
            
            <motion.div
              className="fixed top-0 left-0 bottom-0 w-3/4 bg-gray-900 z-50 
                shadow-2xl md:hidden"
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            >
              <div className="p-6">
                <h2 className="text-2xl font-bold text-white mb-8 font-cinzel">
                  Menú Principal
                </h2>
                
                <nav className="space-y-4">
                  {NAV_ITEMS.map((item, index) => (
                    <motion.button
                      key={item.id}
                      onClick={() => navigateToItem(item, index)}
                      className={`w-full flex items-center gap-4 p-4 rounded-lg
                        transition-all ${
                        index === activeIndex 
                          ? `bg-gradient-to-r ${item.color} text-white` 
                          : 'bg-gray-800 hover:bg-gray-700 text-gray-300'
                      }`}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      {item.icon}
                      <span className="font-semibold">{item.label}</span>
                    </motion.button>
                  ))}
                </nav>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}