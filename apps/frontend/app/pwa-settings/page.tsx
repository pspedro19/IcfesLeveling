'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Settings,
  Bell,
  Download,
  Wifi,
  WifiOff,
  Database,
  Shield,
  Info,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';
import PushNotificationManager from '@/components/PWA/PushNotificationManager';

interface PWASettings {
  notifications: boolean;
  offlineMode: boolean;
  autoUpdate: boolean;
  dataUsage: 'low' | 'medium' | 'high';
}

export default function PWASettingsPage() {
  const [settings, setSettings] = useState<PWASettings>({
    notifications: true,
    offlineMode: true,
    autoUpdate: true,
    dataUsage: 'medium'
  });
  
  const [isOnline, setIsOnline] = useState(true);
  const [cacheSize, setCacheSize] = useState('0 MB');
  const [isInstalled, setIsInstalled] = useState(false);

  useEffect(() => {
    checkOnlineStatus();
    checkInstallStatus();
    calculateCacheSize();
    
    // Listen for online/offline events
    window.addEventListener('online', () => setIsOnline(true));
    window.addEventListener('offline', () => setIsOnline(false));
    
    return () => {
      window.removeEventListener('online', () => setIsOnline(true));
      window.removeEventListener('offline', () => setIsOnline(false));
    };
  }, []);

  const checkOnlineStatus = () => {
    setIsOnline(navigator.onLine);
  };

  const checkInstallStatus = () => {
    // Check if app is installed as PWA
    if (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) {
      setIsInstalled(true);
    }
  };

  const calculateCacheSize = async () => {
    try {
      if ('caches' in window) {
        const cacheNames = await caches.keys();
        let totalSize = 0;
        
        for (const cacheName of cacheNames) {
          const cache = await caches.open(cacheName);
          const requests = await cache.keys();
          
          for (const request of requests) {
            const response = await cache.match(request);
            if (response) {
              const blob = await response.blob();
              totalSize += blob.size;
            }
          }
        }
        
        setCacheSize(`${(totalSize / (1024 * 1024)).toFixed(2)} MB`);
      }
    } catch (error) {
      console.error('Error calculating cache size:', error);
    }
  };

  const handleSettingChange = (key: keyof PWASettings, value: any) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
    
    // Save to localStorage
    localStorage.setItem('pwa-settings', JSON.stringify({
      ...settings,
      [key]: value
    }));
  };

  const clearCache = async () => {
    try {
      if ('caches' in window) {
        const cacheNames = await caches.keys();
        await Promise.all(
          cacheNames.map(cacheName => caches.delete(cacheName))
        );
        setCacheSize('0 MB');
        
        // Show success message
        alert('Cache limpiado exitosamente');
      }
    } catch (error) {
      console.error('Error clearing cache:', error);
      alert('Error al limpiar el cache');
    }
  };

  const installPWA = () => {
    // Trigger PWA install prompt
    const deferredPrompt = (window as any).deferredPrompt;
    if (deferredPrompt) {
      deferredPrompt.prompt();
      deferredPrompt.userChoice.then((choiceResult: any) => {
        if (choiceResult.outcome === 'accepted') {
          console.log('PWA installed');
          setIsInstalled(true);
        }
        (window as any).deferredPrompt = null;
      });
    } else {
      alert('La instalación PWA no está disponible en este momento');
    }
  };

  const getDataUsageDescription = (usage: string) => {
    switch (usage) {
      case 'low':
        return 'Optimizado para conexiones lentas. Menos funcionalidades offline.';
      case 'medium':
        return 'Balance entre rendimiento y funcionalidad. Recomendado.';
      case 'high':
        return 'Máxima funcionalidad offline. Mayor uso de datos.';
      default:
        return '';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div
          className="bg-gray-900/90 rounded-lg p-6 mb-6 border border-purple-500/30"
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
        >
          <div className="flex items-center gap-3 mb-4">
            <Settings className="w-8 h-8 text-purple-400" />
            <h1 className="text-3xl font-bold text-white">
              Configuración PWA
            </h1>
          </div>
          
          <div className="flex items-center gap-4 text-sm">
            <div className={`flex items-center gap-2 ${isOnline ? 'text-green-400' : 'text-red-400'}`}>
              {isOnline ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
              <span>{isOnline ? 'En línea' : 'Sin conexión'}</span>
            </div>
            
            <div className="flex items-center gap-2 text-blue-400">
              <Database className="w-4 h-4" />
              <span>Cache: {cacheSize}</span>
            </div>
            
            {isInstalled && (
              <div className="flex items-center gap-2 text-green-400">
                <CheckCircle className="w-4 h-4" />
                <span>Instalado como PWA</span>
              </div>
            )}
          </div>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Notifications Section */}
          <motion.div
            className="bg-gray-900/90 rounded-lg p-6 border border-purple-500/30"
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.1 }}
          >
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <Bell className="w-5 h-5" />
              Notificaciones
            </h2>
            
            <PushNotificationManager />
          </motion.div>

          {/* Offline Settings */}
          <motion.div
            className="bg-gray-900/90 rounded-lg p-6 border border-purple-500/30"
            initial={{ x: 20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <WifiOff className="w-5 h-5" />
              Modo Offline
            </h2>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-white">Habilitar modo offline</h3>
                  <p className="text-sm text-gray-400">
                    Permite usar la app sin conexión
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.offlineMode}
                    onChange={(e) => handleSettingChange('offlineMode', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                </label>
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-white">Actualización automática</h3>
                  <p className="text-sm text-gray-400">
                    Descarga actualizaciones automáticamente
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.autoUpdate}
                    onChange={(e) => handleSettingChange('autoUpdate', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                </label>
              </div>
            </div>
          </motion.div>

          {/* Data Usage Settings */}
          <motion.div
            className="bg-gray-900/90 rounded-lg p-6 border border-purple-500/30"
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <Database className="w-5 h-5" />
              Uso de Datos
            </h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-white mb-2">
                  Nivel de funcionalidad offline
                </label>
                <select
                  value={settings.dataUsage}
                  onChange={(e) => handleSettingChange('dataUsage', e.target.value)}
                  className="w-full bg-gray-800 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="low">Bajo (Ahorro de datos)</option>
                  <option value="medium">Medio (Recomendado)</option>
                  <option value="high">Alto (Máxima funcionalidad)</option>
                </select>
                <p className="text-sm text-gray-400 mt-2">
                  {getDataUsageDescription(settings.dataUsage)}
                </p>
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-white">Notificaciones</h3>
                  <p className="text-sm text-gray-400">
                    Recibir notificaciones push
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.notifications}
                    onChange={(e) => handleSettingChange('notifications', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                </label>
              </div>
            </div>
          </motion.div>

          {/* Cache Management */}
          <motion.div
            className="bg-gray-900/90 rounded-lg p-6 border border-purple-500/30"
            initial={{ x: 20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.4 }}
          >
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <Shield className="w-5 h-5" />
              Gestión de Cache
            </h2>
            
            <div className="space-y-4">
              <div className="bg-gray-800/50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white font-semibold">Tamaño del cache</span>
                  <span className="text-blue-400 font-mono">{cacheSize}</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${Math.min(parseFloat(cacheSize) * 10, 100)}%` }}
                  />
                </div>
              </div>
              
              <div className="flex gap-3">
                <button
                  onClick={clearCache}
                  className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold transition-all"
                >
                  Limpiar Cache
                </button>
                
                <button
                  onClick={calculateCacheSize}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-semibold transition-all"
                >
                  Actualizar
                </button>
              </div>
              
              {!isInstalled && (
                <div className="mt-4">
                  <button
                    onClick={installPWA}
                    className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-all flex items-center justify-center gap-2"
                  >
                    <Download className="w-4 h-4" />
                    Instalar como App
                  </button>
                </div>
              )}
            </div>
          </motion.div>
        </div>

        {/* Info Section */}
        <motion.div
          className="mt-6 bg-gray-900/90 rounded-lg p-6 border border-purple-500/30"
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-blue-400 mt-0.5" />
            <div>
              <h3 className="font-semibold text-white mb-2">
                Acerca de ICFES Leveling PWA
              </h3>
              <div className="space-y-2 text-sm text-gray-300">
                <p>
                  ICFES Leveling es una Progressive Web App (PWA) que te permite:
                </p>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>Usar la app sin conexión a internet</li>
                  <li>Recibir notificaciones push de actividades</li>
                  <li>Instalar la app en tu dispositivo</li>
                  <li>Acceso rápido desde la pantalla de inicio</li>
                  <li>Sincronización automática cuando vuelves a estar en línea</li>
                </ul>
                <p className="mt-3 text-xs text-gray-400">
                  Versión: 1.0.0 • Última actualización: {new Date().toLocaleDateString()}
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
} 