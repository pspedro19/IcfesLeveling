'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Menu, X, ChevronLeft, ChevronRight } from 'lucide-react';

interface ResponsiveDashboardProps {
  children: React.ReactNode;
  sidebar?: React.ReactNode;
  header?: React.ReactNode;
  className?: string;
}

export default function ResponsiveDashboard({
  children,
  sidebar,
  header,
  className = ''
}: ResponsiveDashboardProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  // Handle responsive behavior
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (mobile) {
        setSidebarOpen(false);
        setSidebarCollapsed(false);
      }
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Close sidebar when clicking outside on mobile
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (isMobile && sidebarOpen) {
        const sidebar = document.getElementById('dashboard-sidebar');
        const target = event.target as Node;
        if (sidebar && !sidebar.contains(target)) {
          setSidebarOpen(false);
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isMobile, sidebarOpen]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 'b':
            e.preventDefault();
            if (isMobile) {
              setSidebarOpen(!sidebarOpen);
            } else {
              setSidebarCollapsed(!sidebarCollapsed);
            }
            break;
        }
      }
      if (e.key === 'Escape' && isMobile && sidebarOpen) {
        setSidebarOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [isMobile, sidebarOpen, sidebarCollapsed]);

  return (
    <div className={`min-h-screen bg-gray-950 text-white flex relative ${className}`}>
      {/* Mobile Overlay */}
      {isMobile && sidebarOpen && (
        <motion.div
          className="fixed inset-0 bg-black/50 z-40"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      {sidebar && (
        <motion.aside
          id="dashboard-sidebar"
          className={`
            ${isMobile 
              ? 'fixed left-0 top-0 h-full z-50' 
              : 'relative'
            }
            ${isMobile && !sidebarOpen ? '-translate-x-full' : 'translate-x-0'}
            ${!isMobile && sidebarCollapsed ? 'w-16' : 'w-64'}
            bg-gray-900/95 border-r border-gray-700/50 transition-all duration-300
          `}
          initial={false}
          animate={{
            width: isMobile ? 256 : (sidebarCollapsed ? 64 : 256),
            x: isMobile && !sidebarOpen ? -256 : 0
          }}
          transition={{ duration: 0.3 }}
        >
          {/* Sidebar Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-700/50">
            {!sidebarCollapsed && (
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">IL</span>
                </div>
                <span className="text-white font-bold">IcfesLeveling</span>
              </div>
            )}
            
            {/* Collapse/Expand Button */}
            <button
              onClick={() => {
                if (isMobile) {
                  setSidebarOpen(false);
                } else {
                  setSidebarCollapsed(!sidebarCollapsed);
                }
              }}
              className="p-1 hover:bg-gray-800 rounded transition-colors"
              title={isMobile ? 'Cerrar' : (sidebarCollapsed ? 'Expandir' : 'Contraer')}
            >
              {isMobile ? (
                <X className="w-4 h-4 text-gray-400" />
              ) : sidebarCollapsed ? (
                <ChevronRight className="w-4 h-4 text-gray-400" />
              ) : (
                <ChevronLeft className="w-4 h-4 text-gray-400" />
              )}
            </button>
          </div>

          {/* Sidebar Content */}
          <div className="flex-1 overflow-y-auto">
            {sidebar}
          </div>

          {/* Keyboard Shortcut Hint */}
          {!isMobile && !sidebarCollapsed && (
            <div className="p-4 border-t border-gray-700/50">
              <div className="text-xs text-gray-500 text-center">
                <kbd className="px-2 py-1 bg-gray-800 rounded text-xs">Ctrl</kbd> + 
                <kbd className="px-2 py-1 bg-gray-800 rounded text-xs ml-1">B</kbd>
                <p className="mt-1">para contraer</p>
              </div>
            </div>
          )}
        </motion.aside>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        {header && (
          <header className="bg-gray-900/95 border-b border-gray-700/50 px-4 md:px-6 py-4">
            <div className="flex items-center gap-4">
              {/* Mobile Menu Button */}
              {isMobile && sidebar && (
                <button
                  onClick={() => setSidebarOpen(true)}
                  className="p-2 hover:bg-gray-800 rounded-lg transition-colors md:hidden"
                  aria-label="Abrir menú"
                >
                  <Menu className="w-5 h-5 text-gray-400" />
                </button>
              )}
              
              {/* Header Content */}
              <div className="flex-1 min-w-0">
                {header}
              </div>
            </div>
          </header>
        )}

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="p-4 md:p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

// Hook for responsive utilities
export function useResponsive() {
  const [breakpoint, setBreakpoint] = useState<'mobile' | 'tablet' | 'desktop'>('desktop');
  const [isMobile, setIsMobile] = useState(false);
  const [isTablet, setIsTablet] = useState(false);
  const [isDesktop, setIsDesktop] = useState(true);

  useEffect(() => {
    const updateBreakpoint = () => {
      const width = window.innerWidth;
      
      if (width < 768) {
        setBreakpoint('mobile');
        setIsMobile(true);
        setIsTablet(false);
        setIsDesktop(false);
      } else if (width < 1024) {
        setBreakpoint('tablet');
        setIsMobile(false);
        setIsTablet(true);
        setIsDesktop(false);
      } else {
        setBreakpoint('desktop');
        setIsMobile(false);
        setIsTablet(false);
        setIsDesktop(true);
      }
    };

    updateBreakpoint();
    window.addEventListener('resize', updateBreakpoint);
    return () => window.removeEventListener('resize', updateBreakpoint);
  }, []);

  return {
    breakpoint,
    isMobile,
    isTablet,
    isDesktop,
    // Utility functions
    getGridCols: (mobile: number, tablet: number, desktop: number) => {
      if (isMobile) return mobile;
      if (isTablet) return tablet;
      return desktop;
    },
    getSpacing: (mobile: string, tablet: string, desktop: string) => {
      if (isMobile) return mobile;
      if (isTablet) return tablet;
      return desktop;
    }
  };
}

// Responsive Grid Component
interface ResponsiveGridProps {
  children: React.ReactNode;
  cols?: {
    mobile?: number;
    tablet?: number;
    desktop?: number;
  };
  gap?: string;
  className?: string;
}

export function ResponsiveGrid({ 
  children, 
  cols = { mobile: 1, tablet: 2, desktop: 3 },
  gap = 'gap-4',
  className = ''
}: ResponsiveGridProps) {
  const { getGridCols } = useResponsive();
  
  const gridCols = getGridCols(
    cols.mobile || 1,
    cols.tablet || 2,
    cols.desktop || 3
  );

  return (
    <div 
      className={`grid ${gap} ${className}`}
      style={{ 
        gridTemplateColumns: `repeat(${gridCols}, minmax(0, 1fr))` 
      }}
    >
      {children}
    </div>
  );
}

// Responsive Card Component
interface ResponsiveCardProps {
  children: React.ReactNode;
  className?: string;
  padding?: {
    mobile?: string;
    tablet?: string;
    desktop?: string;
  };
}

export function ResponsiveCard({ 
  children, 
  className = '',
  padding = { mobile: 'p-4', tablet: 'p-5', desktop: 'p-6' }
}: ResponsiveCardProps) {
  const { getSpacing } = useResponsive();
  
  const cardPadding = getSpacing(
    padding.mobile || 'p-4',
    padding.tablet || 'p-5',
    padding.desktop || 'p-6'
  );

  return (
    <div className={`bg-gray-900/80 rounded-xl border border-gray-700/50 ${cardPadding} ${className}`}>
      {children}
    </div>
  );
}