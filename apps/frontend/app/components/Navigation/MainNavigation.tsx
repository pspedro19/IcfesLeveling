'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Home,
  User,
  BookOpen,
  Trophy,
  BarChart3,
  Users,
  Settings,
  LogOut,
  Menu,
  X,
  Zap,
  Shield,
  Star,
  Sparkles,
  Target,
  Gamepad2,
  GraduationCap,
  Crown
} from 'lucide-react';
import { routes } from '../../routes';
import { authService } from '../../services/auth.service';

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
  requiresAuth?: boolean;
  adminOnly?: boolean;
}

const navigationItems: NavItem[] = [
  { label: 'Home', href: routes.home, icon: Home },
  { label: 'Student Dashboard', href: routes.studentDashboard, icon: User, requiresAuth: true },
  { label: 'Teacher Dashboard', href: routes.teacherDashboard, icon: GraduationCap, adminOnly: true },
  { label: 'Diagnostic Test', href: routes.diagnosticTest, icon: Target, requiresAuth: true },
  { label: 'Study Plans', href: routes.studyPlans, icon: BookOpen, requiresAuth: true },
  { label: 'Dungeon', href: routes.dungeon, icon: Shield, requiresAuth: true, badge: 'NEW' },
  { label: 'Boss Battles', href: routes.bossBattles, icon: Gamepad2, requiresAuth: true },
  { label: 'Achievements', href: routes.achievements, icon: Trophy, requiresAuth: true },
  { label: 'Leaderboards', href: routes.leaderboards, icon: Crown, requiresAuth: true },
  { label: 'Analytics', href: routes.analytics, icon: BarChart3, requiresAuth: true },
  { label: 'Guilds', href: routes.guilds, icon: Users, requiresAuth: true },
  { label: 'Premium', href: routes.premium, icon: Star, badge: 'HOT' },
];

export default function MainNavigation() {
  const [isOpen, setIsOpen] = useState(false);
  const pathname = usePathname();
  const isAuthenticated = authService.isAuthenticated();
  const user = typeof window !== 'undefined' ? JSON.parse(localStorage.getItem('user') || '{}') : {};
  const isAdmin = user?.role === 'admin' || user?.is_admin;

  const filteredItems = navigationItems.filter(item => {
    if (item.adminOnly && !isAdmin) return false;
    if (item.requiresAuth && !isAuthenticated) return false;
    return true;
  });

  const handleLogout = () => {
    authService.logout();
  };

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed top-4 left-4 z-50 md:hidden bg-gradient-to-r from-purple-600 to-blue-600 p-3 rounded-lg shadow-lg"
      >
        {isOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Navigation Sidebar */}
      <AnimatePresence>
        {(isOpen || window.innerWidth >= 768) && (
          <motion.div
            initial={{ x: -300 }}
            animate={{ x: 0 }}
            exit={{ x: -300 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            className="fixed left-0 top-0 h-full w-64 bg-gradient-to-b from-gray-900 to-black border-r border-purple-500/30 z-40 overflow-y-auto"
          >
            {/* Logo/Title */}
            <div className="p-6 border-b border-purple-500/30">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-gold-400 to-purple-400 bg-clip-text text-transparent flex items-center gap-2">
                <Sparkles className="w-6 h-6" />
                IcfesLeveling
              </h1>
              {isAuthenticated && user?.username && (
                <p className="text-sm text-gray-400 mt-2">
                  Welcome, {user.username}
                </p>
              )}
            </div>

            {/* Navigation Items */}
            <nav className="p-4">
              <div className="space-y-2">
                {filteredItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.href;
                  
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`
                        flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200
                        ${isActive 
                          ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg' 
                          : 'hover:bg-purple-600/20 text-gray-300 hover:text-white'
                        }
                      `}
                      onClick={() => setIsOpen(false)}
                    >
                      <Icon size={20} />
                      <span className="flex-1">{item.label}</span>
                      {item.badge && (
                        <span className={`
                          text-xs px-2 py-1 rounded-full
                          ${item.badge === 'NEW' ? 'bg-green-500' : 'bg-orange-500'}
                        `}>
                          {item.badge}
                        </span>
                      )}
                    </Link>
                  );
                })}
              </div>

              {/* Auth Actions */}
              <div className="mt-8 pt-8 border-t border-gray-800">
                {isAuthenticated ? (
                  <>
                    <Link
                      href="/settings"
                      className="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-purple-600/20 hover:text-white transition-all duration-200"
                    >
                      <Settings size={20} />
                      <span>Settings</span>
                    </Link>
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-red-600/20 hover:text-red-400 transition-all duration-200"
                    >
                      <LogOut size={20} />
                      <span>Logout</span>
                    </button>
                  </>
                ) : (
                  <>
                    <Link
                      href={routes.login}
                      className="flex items-center gap-3 px-4 py-3 rounded-lg bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg hover:shadow-xl transition-all duration-200"
                    >
                      <Zap size={20} />
                      <span>Login</span>
                    </Link>
                    <Link
                      href={routes.signup}
                      className="flex items-center gap-3 px-4 py-3 mt-2 rounded-lg border border-purple-500/50 text-purple-400 hover:bg-purple-600/20 transition-all duration-200"
                    >
                      <User size={20} />
                      <span>Sign Up</span>
                    </Link>
                  </>
                )}
              </div>
            </nav>

            {/* User Stats (if authenticated) */}
            {isAuthenticated && user?.level && (
              <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black to-transparent">
                <div className="bg-purple-900/30 rounded-lg p-3 backdrop-blur-sm">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-400">Level</span>
                    <span className="text-gold-400 font-bold">{user.level}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm mt-2">
                    <span className="text-gray-400">Rank</span>
                    <span className="text-purple-400 font-bold">{user.rank || 'Novice'}</span>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
}