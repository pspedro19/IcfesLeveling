'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Database,
  RefreshCw,
  Zap,
  Clock,
  CheckCircle,
  XCircle,
  BarChart,
  User,
  Swords,
  MessageSquare,
  Loader2
} from 'lucide-react';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';

interface CacheStats {
  total_cached_profiles?: number;
  total_cached_queries?: number;
  total_cached_pools?: number;
  cache_health: boolean;
  sample_keys?: string[];
}

interface CacheDemoItem {
  title: string;
  description: string;
  endpoint: string;
  icon: React.ReactNode;
  color: string;
}

export default function CacheDemoPage() {
  const [selectedDemo, setSelectedDemo] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [cacheStats, setCacheStats] = useState<CacheStats | null>(null);
  const [responseTime, setResponseTime] = useState<number>(0);
  
  const demos: CacheDemoItem[] = [
    {
      title: 'Perfil de Usuario',
      description: 'Cachea perfiles de usuario para acceso rápido',
      endpoint: '/users/cached/profile/me',
      icon: <User className="w-6 h-6" />,
      color: 'purple'
    },
    {
      title: 'Pool de Preguntas',
      description: 'Cachea preguntas por materia y dificultad',
      endpoint: '/questions/cached/subject/math-subject-id?difficulty=5',
      icon: <MessageSquare className="w-6 h-6" />,
      color: 'blue'
    },
    {
      title: 'Estado de Batalla',
      description: 'Mantiene el estado de batallas activas en caché',
      endpoint: '/battles/cached/state',
      icon: <Swords className="w-6 h-6" />,
      color: 'red'
    },
    {
      title: 'Estadísticas de Caché',
      description: 'Muestra estadísticas del sistema de caché',
      endpoint: '/users/cached/cache/stats',
      icon: <BarChart className="w-6 h-6" />,
      color: 'green'
    }
  ];
  
  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  };
  
  const executeDemo = async (demo: CacheDemoItem) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setSelectedDemo(demo.title);
    
    const startTime = Date.now();
    
    try {
      const response = await axios.get(
        `${API_URL}/api/v1${demo.endpoint}`,
        { headers: getAuthHeaders() }
      );
      
      const endTime = Date.now();
      setResponseTime(endTime - startTime);
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error ejecutando demo');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  const fetchCacheStats = async () => {
    try {
      const response = await axios.get(
        `${API_URL}/api/v1/users/cached/cache/stats`,
        { headers: getAuthHeaders() }
      );
      setCacheStats(response.data);
    } catch (err) {
      console.error('Error fetching cache stats:', err);
    }
  };
  
  const invalidateCache = async () => {
    setLoading(true);
    try {
      await axios.post(
        `${API_URL}/api/v1/users/cached/cache/invalidate-all`,
        {},
        { headers: getAuthHeaders() }
      );
      setResult({ message: 'Caché invalidado exitosamente' });
      await fetchCacheStats();
    } catch (err) {
      setError('Error invalidando caché');
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    fetchCacheStats();
  }, []);
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 
      to-gray-900 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 
            bg-red-600 rounded-full mb-4">
            <Database className="w-10 h-10 text-white" />
          </div>
          
          <h1 className="text-4xl font-bold text-white mb-4 font-cinzel">
            Sistema de Caché Redis
          </h1>
          
          <p className="text-gray-300 max-w-2xl mx-auto">
            Sistema de caché optimizado para mejorar el rendimiento y reducir 
            la carga en la base de datos.
          </p>
        </div>
        
        {/* Cache Health Status */}
        {cacheStats && (
          <div className="bg-gray-900/80 rounded-lg p-6 mb-8 border 
            border-gray-700">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-full ${
                  cacheStats.cache_health ? 'bg-green-600' : 'bg-red-600'
                }`}>
                  {cacheStats.cache_health ? (
                    <CheckCircle className="w-6 h-6 text-white" />
                  ) : (
                    <XCircle className="w-6 h-6 text-white" />
                  )}
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white">
                    Estado del Caché
                  </h3>
                  <p className="text-sm text-gray-400">
                    {cacheStats.cache_health ? 'Operacional' : 'Error de conexión'}
                  </p>
                </div>
              </div>
              
              <button
                onClick={invalidateCache}
                disabled={loading}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white 
                  rounded-lg transition-all disabled:opacity-50 
                  disabled:cursor-not-allowed"
              >
                Invalidar Todo el Caché
              </button>
            </div>
            
            {/* Cache Statistics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
              <div className="bg-gray-800 rounded-lg p-4">
                <p className="text-gray-400 text-sm">Perfiles en Caché</p>
                <p className="text-2xl font-bold text-white">
                  {cacheStats.total_cached_profiles || 0}
                </p>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4">
                <p className="text-gray-400 text-sm">Consultas en Caché</p>
                <p className="text-2xl font-bold text-white">
                  {cacheStats.total_cached_queries || 0}
                </p>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4">
                <p className="text-gray-400 text-sm">Pools de Preguntas</p>
                <p className="text-2xl font-bold text-white">
                  {cacheStats.total_cached_pools || 0}
                </p>
              </div>
            </div>
          </div>
        )}
        
        {/* Demo Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {demos.map((demo, index) => (
            <motion.button
              key={demo.title}
              onClick={() => executeDemo(demo)}
              disabled={loading}
              className={`bg-gray-900/80 hover:bg-gray-800/80 rounded-lg p-6 
                text-left transition-all border border-${demo.color}-500/30
                disabled:opacity-50 disabled:cursor-not-allowed`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <div className="flex items-start gap-4">
                <div className={`p-3 rounded-lg bg-${demo.color}-600/20`}>
                  {demo.icon}
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-white mb-2">
                    {demo.title}
                  </h3>
                  <p className="text-sm text-gray-400">
                    {demo.description}
                  </p>
                  <code className="text-xs text-purple-400 mt-2 block">
                    {demo.endpoint}
                  </code>
                </div>
              </div>
            </motion.button>
          ))}
        </div>
        
        {/* Results Display */}
        {(loading || result || error) && (
          <motion.div
            className="bg-gray-900/80 rounded-lg p-6 border border-gray-700"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            {loading && (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-8 h-8 text-purple-400 animate-spin" />
              </div>
            )}
            
            {!loading && error && (
              <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-4">
                <p className="text-red-400">{error}</p>
              </div>
            )}
            
            {!loading && result && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-semibold text-white">
                    Resultado: {selectedDemo}
                  </h3>
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 text-green-400">
                      <Clock className="w-5 h-5" />
                      <span className="font-semibold">{responseTime}ms</span>
                    </div>
                    <div className="flex items-center gap-2 text-purple-400">
                      <Zap className="w-5 h-5" />
                      <span className="text-sm">
                        {responseTime < 50 ? 'Desde Caché' : 'Desde DB'}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-800 rounded-lg p-4 overflow-auto max-h-96">
                  <pre className="text-sm text-gray-300">
                    {JSON.stringify(result, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </motion.div>
        )}
        
        {/* Info Section */}
        <div className="mt-8 bg-gray-900/80 rounded-lg p-6 border border-gray-700">
          <h3 className="text-xl font-semibold text-white mb-4">
            ¿Cómo funciona el Sistema de Caché?
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-gray-300">
            <div>
              <h4 className="font-semibold text-white mb-2">
                Estrategias de Caché:
              </h4>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <span className="text-purple-400">•</span>
                  <span>
                    <strong>Cache-Aside:</strong> Lee del caché primero, 
                    si no existe, consulta la DB y actualiza el caché
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-400">•</span>
                  <span>
                    <strong>TTL Variable:</strong> Diferentes tiempos de 
                    expiración según el tipo de dato
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-400">•</span>
                  <span>
                    <strong>Invalidación Activa:</strong> Se invalida el 
                    caché cuando los datos cambian
                  </span>
                </li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold text-white mb-2">
                Beneficios de Rendimiento:
              </h4>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <span className="text-green-400">•</span>
                  <span>
                    Respuestas 10-100x más rápidas desde caché
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400">•</span>
                  <span>
                    Reduce la carga en la base de datos principal
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400">•</span>
                  <span>
                    Mejora la escalabilidad del sistema
                  </span>
                </li>
              </ul>
            </div>
          </div>
          
          <div className="mt-6 p-4 bg-purple-900/20 rounded-lg border 
            border-purple-500/30">
            <p className="text-sm text-purple-300">
              <strong>Nota:</strong> Las respuestas desde caché típicamente 
              toman menos de 50ms, mientras que las consultas a la base de 
              datos pueden tomar 100-500ms o más.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}