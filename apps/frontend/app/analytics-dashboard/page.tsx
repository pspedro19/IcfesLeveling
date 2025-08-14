'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  BarChart2, 
  TrendingUp, 
  Users, 
  Activity,
  Shield,
  ChevronRight
} from 'lucide-react';
import AnalyticsDashboard from '@/components/Analytics/AnalyticsDashboard';
import { useAuthStore } from '@/stores/useAuthStore';
import { clickhouseService } from '@/services/clickhouse.service';

export default function AnalyticsPage() {
  const { user } = useAuthStore();
  const [activeUsers, setActiveUsers] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  
  // Fetch real-time active users
  useEffect(() => {
    const fetchActiveUsers = async () => {
      try {
        const data = await clickhouseService.getActiveUsers();
        setActiveUsers(data.activeUsers);
      } catch (error) {
        console.error('Error fetching active users:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchActiveUsers();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchActiveUsers, 30000);
    return () => clearInterval(interval);
  }, []);
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 
      to-gray-900 relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-0 w-96 h-96 bg-purple-600/20 
          rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-blue-600/20 
          rounded-full blur-3xl animate-pulse animation-delay-2000" />
      </div>
      
      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div 
          className="mb-8"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="flex items-center gap-2 text-gray-400 mb-4">
            <span>Dashboard</span>
            <ChevronRight className="w-4 h-4" />
            <span className="text-white">Analytics</span>
          </div>
          
          <div className="flex flex-col md:flex-row md:items-center 
            md:justify-between gap-6">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2 font-cinzel 
                flex items-center gap-4">
                <BarChart2 className="w-10 h-10 text-purple-400" />
                Centro de Analytics
              </h1>
              <p className="text-gray-300">
                Analiza tu progreso y mejora tu rendimiento
              </p>
            </div>
            
            {/* Real-time Stats */}
            <div className="flex items-center gap-6">
              <div className="bg-gray-900/80 rounded-lg px-6 py-4 
                border border-purple-500/30">
                <div className="flex items-center gap-3">
                  <Users className="w-6 h-6 text-green-400" />
                  <div>
                    <p className="text-sm text-gray-400">Usuarios Activos</p>
                    <p className="text-2xl font-bold text-white">
                      {loading ? '...' : activeUsers}
                    </p>
                  </div>
                </div>
              </div>
              
              {user?.isAdmin && (
                <div className="bg-gray-900/80 rounded-lg px-6 py-4 
                  border border-yellow-500/30">
                  <div className="flex items-center gap-3">
                    <Shield className="w-6 h-6 text-yellow-400" />
                    <div>
                      <p className="text-sm text-gray-400">Modo</p>
                      <p className="text-lg font-semibold text-yellow-400">
                        Admin
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </motion.div>
        
        {/* Quick Stats */}
        <motion.div 
          className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="bg-gradient-to-br from-purple-600/20 to-purple-700/20 
            rounded-lg p-6 border border-purple-500/30">
            <Activity className="w-8 h-8 text-purple-400 mb-3" />
            <h3 className="text-lg font-semibold text-white mb-1">
              Batallas Hoy
            </h3>
            <p className="text-3xl font-bold text-purple-400">12</p>
          </div>
          
          <div className="bg-gradient-to-br from-blue-600/20 to-blue-700/20 
            rounded-lg p-6 border border-blue-500/30">
            <TrendingUp className="w-8 h-8 text-blue-400 mb-3" />
            <h3 className="text-lg font-semibold text-white mb-1">
              Precisión
            </h3>
            <p className="text-3xl font-bold text-blue-400">85%</p>
          </div>
          
          <div className="bg-gradient-to-br from-green-600/20 to-green-700/20 
            rounded-lg p-6 border border-green-500/30">
            <BarChart2 className="w-8 h-8 text-green-400 mb-3" />
            <h3 className="text-lg font-semibold text-white mb-1">
              Experiencia
            </h3>
            <p className="text-3xl font-bold text-green-400">1,250</p>
          </div>
          
          <div className="bg-gradient-to-br from-orange-600/20 to-orange-700/20 
            rounded-lg p-6 border border-orange-500/30">
            <span className="text-3xl mb-3 block">🔥</span>
            <h3 className="text-lg font-semibold text-white mb-1">
              Racha
            </h3>
            <p className="text-3xl font-bold text-orange-400">7 días</p>
          </div>
        </motion.div>
        
        {/* Main Analytics Dashboard */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <AnalyticsDashboard isAdmin={user?.isAdmin || false} />
        </motion.div>
      </div>
    </div>
  );
}