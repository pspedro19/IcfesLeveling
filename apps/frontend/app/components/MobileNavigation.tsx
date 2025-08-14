'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { 
  Home, 
  BookOpen, 
  Trophy, 
  Target, 
  User,
  Bell
} from 'lucide-react';

interface NavItemProps {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  badge?: number;
  onClick: () => void;
}

function NavItem({ icon, label, active, badge, onClick }: NavItemProps) {
  return (
    <motion.button
      onClick={onClick}
      className="flex flex-col items-center gap-1 p-2 relative"
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
    >
      <div className="relative">
        <div className={`p-2 rounded-lg transition-colors ${
          active 
            ? 'bg-teal-100 dark:bg-teal-900/30 text-teal-600 dark:text-teal-400' 
            : 'text-gray-500 dark:text-gray-400'
        }`}>
          {icon}
        </div>
        
        {/* Badge */}
        {badge && badge > 0 && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white 
                       text-xs rounded-full flex items-center justify-center font-bold"
          >
            {badge > 99 ? '99+' : badge}
          </motion.div>
        )}
      </div>
      
      <span className={`text-xs font-medium ${
        active 
          ? 'text-teal-600 dark:text-teal-400' 
          : 'text-gray-500 dark:text-gray-400'
      }`}>
        {label}
      </span>
    </motion.button>
  );
}

interface MobileNavigationProps {
  currentPage: string;
  onPageChange: (page: string) => void;
  notifications?: {
    learn: number;
    progress: number;
    challenges: number;
    profile: number;
  };
  className?: string;
}

export function MobileNavigation({ 
  currentPage, 
  onPageChange, 
  notifications = {},
  className = '' 
}: MobileNavigationProps) {
  const navItems = [
    { id: 'home', icon: <Home className="w-5 h-5" />, label: 'Inicio' },
    { 
      id: 'learn', 
      icon: <BookOpen className="w-5 h-5" />, 
      label: 'Aprender',
      badge: notifications.learn
    },
    { 
      id: 'progress', 
      icon: <Trophy className="w-5 h-5" />, 
      label: 'Progreso',
      badge: notifications.progress
    },
    { 
      id: 'challenges', 
      icon: <Target className="w-5 h-5" />, 
      label: 'Desafíos',
      badge: notifications.challenges
    },
    { 
      id: 'profile', 
      icon: <User className="w-5 h-5" />, 
      label: 'Perfil',
      badge: notifications.profile
    }
  ];

  return (
    <div className={`fixed bottom-0 left-0 right-0 md:hidden 
                    bg-white dark:bg-gray-800 border-t border-gray-200 
                    dark:border-gray-700 z-40 ${className}`}>
      <div className="grid grid-cols-5 gap-1 p-2">
        {navItems.map((item) => (
          <NavItem
            key={item.id}
            icon={item.icon}
            label={item.label}
            active={currentPage === item.id}
            badge={item.badge}
            onClick={() => onPageChange(item.id)}
          />
        ))}
      </div>
      
      {/* Active indicator */}
      <motion.div
        className="absolute top-0 left-0 h-1 bg-gradient-to-r from-teal-500 to-blue-500"
        initial={false}
        animate={{
          x: `${(navItems.findIndex(item => item.id === currentPage) * 100) / 5}%`,
          width: '20%'
        }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
      />
    </div>
  );
}
