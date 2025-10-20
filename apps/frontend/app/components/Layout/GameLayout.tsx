'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import { ArrowLeft, Home, User, Settings } from 'lucide-react';
import MainNavigation from '../Navigation/MainNavigation';

interface GameLayoutProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  showBackButton?: boolean;
  backPath?: string;
  levelRequired?: number;
  rankRequired?: string[];
  className?: string;
}

export default function GameLayout({
  children,
  title,
  subtitle,
  showBackButton = true,
  backPath,
  levelRequired,
  rankRequired,
  className = ""
}: GameLayoutProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [accessDenied, setAccessDenied] = useState(false);

  useEffect(() => {
    // Load user data
    const userData = localStorage.getItem('currentUser') || localStorage.getItem('user');
    if (userData) {
      try {
        const user = JSON.parse(userData);
        setCurrentUser(user);
        
        // Check access requirements
        if (levelRequired && user.level < levelRequired) {
          setAccessDenied(true);
          return;
        }
        
        if (rankRequired && !rankRequired.includes(user.rank)) {
          setAccessDenied(true);
          return;
        }
      } catch (error) {
        console.error('Error loading user data:', error);
      }
    }
  }, [levelRequired, rankRequired]);

  const getDefaultBackPath = () => {
    // Smart back navigation based on current path
    if (pathname.includes('diagnostic')) return '/hub-central';
    if (pathname.includes('biblioteca')) return '/hub-central';
    if (pathname.includes('arena')) return '/hub-central';
    if (pathname.includes('santuario')) return '/hub-central';
    if (pathname.includes('mazmorra')) return '/hub-central';
    if (pathname.includes('torre')) return '/hub-central';
    return '/hub-central';
  };

  const handleBackClick = () => {
    const targetPath = backPath || getDefaultBackPath();
    router.push(targetPath);
  };

  // Access Denied Screen
  if (accessDenied) {
    const requirements = [];
    if (levelRequired) requirements.push(`Nivel ${levelRequired}`);
    if (rankRequired) requirements.push(`Rango ${rankRequired.join(' o ')}`);
    
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white">
        <MainNavigation currentUser={currentUser} />
        
        <div className="pt-20 lg:pt-24 pb-8">
          <div className="container mx-auto px-4">
            <div className="max-w-2xl mx-auto text-center">
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-red-900/20 rounded-xl p-8 border border-red-500/30"
              >
                <div className="text-6xl mb-4">🔒</div>
                <h1 className="text-3xl font-bold text-red-400 mb-4">Acceso Denegado</h1>
                <p className="text-red-200 mb-6">
                  Esta área requiere:
                </p>
                <div className="space-y-2 mb-6">
                  {requirements.map((req, index) => (
                    <div key={index} className="bg-black/30 rounded-lg p-3">
                      <span className="text-red-300 font-semibold">• {req}</span>
                    </div>
                  ))}
                </div>
                <p className="text-purple-200 mb-6">
                  Tu progreso actual:<br />
                  <span className="font-bold">Nivel {currentUser?.level || 0} • Rango {currentUser?.rank || 'E'}</span>
                </p>
                <button
                  onClick={() => router.push('/hub-central')}
                  className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 px-8 py-3 rounded-lg font-semibold transition-all transform hover:scale-105"
                >
                  🏠 Volver al Hub Central
                </button>
              </motion.div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 text-white ${className}`}>
      <MainNavigation currentUser={currentUser} />
      
      <div className="pt-20 lg:pt-24 pb-8">
        <div className="container mx-auto px-4">
          {/* Header with Back Button */}
          {(title || showBackButton) && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center mb-8"
            >
              {showBackButton && (
                <div className="flex items-center justify-center gap-4 mb-4">
                  <button
                    onClick={handleBackClick}
                    className="bg-purple-600/50 hover:bg-purple-700/50 p-3 rounded-lg transition-all group"
                  >
                    <ArrowLeft className="w-5 h-5 group-hover:translate-x-[-2px] transition-transform" />
                  </button>
                  
                  {title && (
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-gold-400 to-purple-400 bg-clip-text text-transparent">
                      {title}
                    </h1>
                  )}
                </div>
              )}
              
              {subtitle && (
                <p className="text-xl text-purple-200">
                  {subtitle}
                </p>
              )}
            </motion.div>
          )}

          {/* Main Content */}
          {children}
        </div>
      </div>

      {/* Quick Navigation Footer */}
      <div className="fixed bottom-4 right-4 z-30">
        <div className="flex flex-col gap-2">
          <button
            onClick={() => router.push('/hub-central')}
            className="bg-purple-600/80 hover:bg-purple-700/80 p-3 rounded-full backdrop-blur-sm border border-purple-500/30 text-white transition-all transform hover:scale-110 shadow-lg"
            title="Hub Central"
          >
            <Home className="w-5 h-5" />
          </button>
          
          {currentUser && (
            <button
              onClick={() => router.push('/profile')}
              className="bg-blue-600/80 hover:bg-blue-700/80 p-3 rounded-full backdrop-blur-sm border border-blue-500/30 text-white transition-all transform hover:scale-110 shadow-lg"
              title="Mi Perfil"
            >
              <User className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
