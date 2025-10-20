'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Home,
  User,
  BookOpen,
  Sword, 
  Trophy,
  Settings,
  LogOut,
  Menu,
  X,
  Crown,
  Shield,
  Zap,
  Star
} from 'lucide-react';

interface NavigationProps {
  currentUser?: {
    id: string;
    username: string;
    level: number;
    rank: string;
    experience: number;
    hp: number;
    mp: number;
  };
}

export default function MainNavigation({ currentUser }: NavigationProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  // Navigation items with level requirements
  const navigationItems = [
    {
      id: 'home',
      label: 'Hub Central',
      icon: Home,
      path: '/hub-central',
      levelRequired: 1,
      description: 'Centro de comando principal'
    },
    {
      id: 'diagnostic',
      label: 'Portal del Despertar',
      icon: Zap,
      path: '/portal-despertar',
      levelRequired: 1,
      description: 'Diagnóstico inicial'
    },
    {
      id: 'library',
      label: 'Biblioteca Ancestral',
      icon: BookOpen,
      path: '/biblioteca-ancestral',
      levelRequired: 5,
      description: 'Videos y recursos por competencia'
    },
    {
      id: 'arena',
      label: 'Arena del Conocimiento',
      icon: Sword,
      path: '/arena-conocimiento',
      levelRequired: 10,
      description: 'Práctica intensiva ICFES'
    },
    {
      id: 'sanctuary',
      label: 'Santuario de la Sabiduría',
      icon: Crown,
      path: '/santuario-sabiduria',
      levelRequired: 20,
      description: 'Reportes PDF y consolidación'
    },
    {
      id: 'dungeon',
      label: 'Mazmorra del Tiempo',
      icon: Shield,
      path: '/mazmorra-tiempo',
      levelRequired: 15,
      description: 'Simulacros cronometrados',
      isSpecialEvent: true
    },
    {
      id: 'tower',
      label: 'Torre de los Monarcas',
      icon: Trophy,
      path: '/torre-monarcas',
      levelRequired: 50,
      rankRequired: ['A', 'S', 'SS', 'SSS'],
      description: 'Desafíos para Rango A/S'
    }
  ];

  const isAreaUnlocked = (item: any) => {
    if (!currentUser) return false;
    
    // Check level requirement
    if (currentUser.level < item.levelRequired) return false;
    
    // Check rank requirement if exists
    if (item.rankRequired && !item.rankRequired.includes(currentUser.rank)) return false;
    
    return true;
  };

  const getRankColor = (rank: string) => {
    const colors = {
      'E': 'text-gray-400',
      'D': 'text-green-400', 
      'C': 'text-blue-400',
      'B': 'text-purple-400',
      'A': 'text-yellow-400',
      'S': 'text-red-400',
      'SS': 'text-pink-400',
      'SSS': 'text-gold-400'
    };
    return colors[rank] || 'text-gray-400';
  };

  const handleNavigation = (item: any) => {
    if (!isAreaUnlocked(item)) {
      // Show unlock requirements
      alert(`🔒 Área Bloqueada\n\nRequisitos:\n• Nivel ${item.levelRequired}\n${item.rankRequired ? `• Rango ${item.rankRequired.join(' o ')}` : ''}\n\nTu nivel actual: ${currentUser?.level || 0}\nTu rango actual: ${currentUser?.rank || 'E'}`);
      return;
    }
    
    setIsOpen(false);
    router.push(item.path);
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('currentUser');
    localStorage.removeItem('user');
    router.push('/login');
  };

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed top-4 left-4 z-50 lg:hidden bg-purple-600/80 backdrop-blur-sm p-3 rounded-lg border border-purple-500/30 text-white hover:bg-purple-700/80 transition-all"
      >
        {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* User Info Button */}
      {currentUser && (
        <button
          onClick={() => setShowUserMenu(!showUserMenu)}
          className="fixed top-4 right-4 z-50 bg-gradient-to-r from-purple-600/80 to-blue-600/80 backdrop-blur-sm p-3 rounded-lg border border-purple-500/30 text-white hover:from-purple-700/80 hover:to-blue-700/80 transition-all flex items-center gap-2"
        >
          <div className="text-right text-sm">
            <div className="font-bold">{currentUser.username}</div>
            <div className={`text-xs ${getRankColor(currentUser.rank)}`}>
              Nivel {currentUser.level} • Rango {currentUser.rank}
            </div>
          </div>
          <User className="w-5 h-5" />
        </button>
      )}

      {/* Navigation Sidebar */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
              onClick={() => setIsOpen(false)}
            />
            
            {/* Sidebar */}
          <motion.div
              initial={{ x: -300, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -300, opacity: 0 }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="fixed left-0 top-0 h-full w-80 bg-gradient-to-b from-gray-900/95 to-purple-900/95 backdrop-blur-xl border-r border-purple-500/30 z-45 overflow-y-auto"
            >
              <div className="p-6">
                {/* Header */}
                <div className="mb-8 text-center">
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-gold-400 to-purple-400 bg-clip-text text-transparent">
                    🎮 ICFES Leveling
              </h1>
                  <p className="text-purple-300 text-sm">Sistema de Entrenamiento Hunter</p>
                </div>

                {/* User Stats */}
                {currentUser && (
                  <div className="mb-6 bg-black/30 rounded-lg p-4 border border-purple-500/30">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center text-white font-bold">
                        {currentUser.username[0].toUpperCase()}
                      </div>
                      <div>
                        <div className="font-bold text-white">{currentUser.username}</div>
                        <div className={`text-sm ${getRankColor(currentUser.rank)}`}>
                          Nivel {currentUser.level} • Rango {currentUser.rank}
                        </div>
                      </div>
            </div>
                    
                    {/* HP/MP Bars */}
                    <div className="space-y-2">
                      <div>
                        <div className="flex justify-between text-xs text-red-300 mb-1">
                          <span>HP</span>
                          <span>{currentUser.hp}/100</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2">
                          <div 
                            className="bg-red-500 h-2 rounded-full transition-all"
                            style={{ width: `${currentUser.hp}%` }}
                          />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-xs text-blue-300 mb-1">
                          <span>MP</span>
                          <span>{currentUser.mp}/50</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2">
                          <div 
                            className="bg-blue-500 h-2 rounded-full transition-all"
                            style={{ width: `${(currentUser.mp / 50) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                )}

            {/* Navigation Items */}
                <nav className="space-y-2">
                  {navigationItems.map((item) => {
                    const isUnlocked = isAreaUnlocked(item);
                    const isActive = pathname === item.path;
                  const Icon = item.icon;
                  
                  return (
                      <motion.button
                        key={item.id}
                        onClick={() => handleNavigation(item)}
                        className={`w-full text-left p-4 rounded-lg border transition-all relative overflow-hidden group ${
                          isActive 
                            ? 'bg-gradient-to-r from-purple-600/50 to-blue-600/50 border-purple-400/50 text-white' 
                            : isUnlocked
                              ? 'bg-black/30 border-purple-500/30 text-purple-100 hover:bg-purple-800/30 hover:border-purple-400/50'
                              : 'bg-gray-900/50 border-gray-600/30 text-gray-500 cursor-not-allowed'
                        }`}
                        whileHover={isUnlocked ? { scale: 1.02 } : {}}
                        whileTap={isUnlocked ? { scale: 0.98 } : {}}
                      >
                        {/* Unlock Effect */}
                        {isUnlocked && (
                          <motion.div
                            className="absolute inset-0 bg-gradient-to-r from-gold-400/20 to-purple-400/20 opacity-0 group-hover:opacity-100 transition-opacity"
                            layoutId={`nav-bg-${item.id}`}
                          />
                        )}
                        
                        <div className="relative flex items-center gap-3">
                          <div className={`p-2 rounded-lg ${
                            isUnlocked 
                              ? 'bg-purple-600/50' 
                              : 'bg-gray-700/50'
                          }`}>
                            <Icon className="w-5 h-5" />
                          </div>
                          
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold">{item.label}</span>
                              {item.isSpecialEvent && (
                                <span className="text-xs bg-yellow-500/80 text-black px-2 py-1 rounded-full font-bold">
                                  EVENTO
                                </span>
                              )}
                              {!isUnlocked && (
                                <span className="text-xs bg-red-500/80 px-2 py-1 rounded-full">
                                  🔒 Nivel {item.levelRequired}
                        </span>
                      )}
                            </div>
                            <div className="text-xs opacity-75 mt-1">
                              {item.description}
                            </div>
                          </div>
                        </div>
                      </motion.button>
                  );
                })}
                </nav>

                {/* Quick Actions */}
                <div className="mt-8 pt-6 border-t border-purple-500/30">
                  <h3 className="text-sm font-semibold text-purple-300 mb-3">Acciones Rápidas</h3>
                  <div className="space-y-2">
                    <button
                      onClick={() => {
                        setIsOpen(false);
                        router.push('/profile');
                      }}
                      className="w-full text-left p-3 rounded-lg bg-black/30 border border-purple-500/30 text-purple-100 hover:bg-purple-800/30 transition-all flex items-center gap-3"
                    >
                      <User className="w-4 h-4" />
                      <span>Mi Perfil</span>
                    </button>
                    
                    <button
                      onClick={() => {
                        setIsOpen(false);
                        router.push('/settings');
                      }}
                      className="w-full text-left p-3 rounded-lg bg-black/30 border border-purple-500/30 text-purple-100 hover:bg-purple-800/30 transition-all flex items-center gap-3"
                    >
                      <Settings className="w-4 h-4" />
                      <span>Configuración</span>
                    </button>
                    
                    <button
                      onClick={handleLogout}
                      className="w-full text-left p-3 rounded-lg bg-red-900/30 border border-red-500/30 text-red-100 hover:bg-red-800/30 transition-all flex items-center gap-3"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Cerrar Sesión</span>
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
                  </>
                )}
      </AnimatePresence>

      {/* User Menu Dropdown */}
      <AnimatePresence>
        {showUserMenu && currentUser && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="fixed top-16 right-4 z-40 bg-gradient-to-b from-gray-900/95 to-purple-900/95 backdrop-blur-xl rounded-lg border border-purple-500/30 p-4 min-w-64"
          >
            <div className="text-center mb-4">
              <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center text-white font-bold text-xl mx-auto mb-2">
                {currentUser.username[0].toUpperCase()}
              </div>
              <div className="font-bold text-white">{currentUser.username}</div>
              <div className={`text-sm ${getRankColor(currentUser.rank)}`}>
                Nivel {currentUser.level} • Rango {currentUser.rank}
              </div>
            </div>
            
            {/* Detailed Stats */}
            <div className="space-y-3 mb-4">
              <div className="bg-black/30 rounded-lg p-3">
                <div className="text-xs text-purple-300 mb-2">Experiencia</div>
                <div className="flex justify-between text-sm">
                  <span className="text-white">{currentUser.experience} XP</span>
                  <span className="text-purple-300">Siguiente: {(Math.floor(currentUser.level / 10) + 1) * 1000}</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2 mt-2">
                  <div 
                    className="bg-gradient-to-r from-purple-500 to-gold-500 h-2 rounded-full"
                    style={{ width: `${(currentUser.experience % 1000) / 10}%` }}
                  />
                </div>
                  </div>
              
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-red-900/30 rounded-lg p-2 text-center">
                  <div className="text-red-300 text-xs">HP</div>
                  <div className="text-white font-bold">{currentUser.hp}</div>
                  </div>
                <div className="bg-blue-900/30 rounded-lg p-2 text-center">
                  <div className="text-blue-300 text-xs">MP</div>
                  <div className="text-white font-bold">{currentUser.mp}</div>
                </div>
              </div>
            </div>
            
            <div className="space-y-2">
              <button
                onClick={() => {
                  setShowUserMenu(false);
                  router.push('/profile');
                }}
                className="w-full text-left p-2 rounded-lg bg-purple-800/30 text-purple-100 hover:bg-purple-700/30 transition-all flex items-center gap-2"
              >
                <User className="w-4 h-4" />
                Ver Perfil Completo
              </button>
              
              <button
                onClick={handleLogout}
                className="w-full text-left p-2 rounded-lg bg-red-800/30 text-red-100 hover:bg-red-700/30 transition-all flex items-center gap-2"
              >
                <LogOut className="w-4 h-4" />
                Cerrar Sesión
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Desktop Navigation Bar */}
      <div className="hidden lg:block fixed top-0 left-0 right-0 z-30 bg-gradient-to-r from-gray-900/80 to-purple-900/80 backdrop-blur-xl border-b border-purple-500/30">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <button
              onClick={() => router.push('/hub-central')}
              className="text-xl font-bold bg-gradient-to-r from-gold-400 to-purple-400 bg-clip-text text-transparent hover:scale-105 transition-transform"
            >
              🎮 ICFES Leveling
            </button>
            
            {/* Navigation Items */}
            <div className="flex items-center gap-2">
              {navigationItems.slice(0, 5).map((item) => {
                const isUnlocked = isAreaUnlocked(item);
                const isActive = pathname === item.path;
                const Icon = item.icon;
                
                return (
                  <button
                    key={item.id}
                    onClick={() => handleNavigation(item)}
                    className={`px-4 py-2 rounded-lg transition-all flex items-center gap-2 text-sm ${
                      isActive
                        ? 'bg-gradient-to-r from-purple-600/50 to-blue-600/50 text-white border border-purple-400/50'
                        : isUnlocked
                          ? 'text-purple-200 hover:bg-purple-800/30 hover:text-white'
                          : 'text-gray-500 cursor-not-allowed'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                    {!isUnlocked && (
                      <span className="text-xs bg-red-500/80 px-1 py-0.5 rounded">
                        {item.levelRequired}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
            
            {/* User Info */}
            {currentUser && (
              <div className="flex items-center gap-4">
                <div className="text-right text-sm">
                  <div className="text-white font-semibold">{currentUser.username}</div>
                  <div className={`text-xs ${getRankColor(currentUser.rank)}`}>
                    Nivel {currentUser.level} • Rango {currentUser.rank}
                  </div>
                </div>
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="w-10 h-10 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center text-white font-bold hover:scale-105 transition-transform"
                >
                  {currentUser.username[0].toUpperCase()}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}