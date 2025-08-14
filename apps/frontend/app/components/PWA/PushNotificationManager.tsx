'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Bell, 
  BellOff, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Settings,
  Zap
} from 'lucide-react';

interface NotificationPermission {
  granted: boolean;
  denied: boolean;
  default: boolean;
}

interface PushNotificationManagerProps {
  onPermissionChange?: (permission: NotificationPermission) => void;
}

export default function PushNotificationManager({ onPermissionChange }: PushNotificationManagerProps) {
  const [permission, setPermission] = useState<NotificationPermission>({
    granted: false,
    denied: false,
    default: false
  });
  const [isSupported, setIsSupported] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  useEffect(() => {
    checkNotificationSupport();
    checkPermissionStatus();
  }, []);

  const checkNotificationSupport = () => {
    const supported = 'Notification' in window && 'serviceWorker' in navigator;
    setIsSupported(supported);
  };

  const checkPermissionStatus = () => {
    if (!isSupported) return;

    const status = Notification.permission;
    const newPermission: NotificationPermission = {
      granted: status === 'granted',
      denied: status === 'denied',
      default: status === 'default'
    };

    setPermission(newPermission);
    onPermissionChange?.(newPermission);
  };

  const requestPermission = async () => {
    if (!isSupported) return;

    setIsLoading(true);
    try {
      const result = await Notification.requestPermission();
      checkPermissionStatus();
      
      if (result === 'granted') {
        // Register service worker for push notifications
        await registerServiceWorker();
        showTestNotification();
      }
    } catch (error) {
      console.error('Error requesting notification permission:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const registerServiceWorker = async () => {
    try {
      if ('serviceWorker' in navigator) {
        const registration = await navigator.serviceWorker.register('/sw.js');
        console.log('Service Worker registered:', registration);
        
        // Subscribe to push notifications
        await subscribeToPushNotifications(registration);
      }
    } catch (error) {
      console.error('Error registering service worker:', error);
    }
  };

  const subscribeToPushNotifications = async (registration: ServiceWorkerRegistration) => {
    try {
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY
      });
      
      console.log('Push notification subscription:', subscription);
      
      // Send subscription to backend
      await sendSubscriptionToServer(subscription);
    } catch (error) {
      console.error('Error subscribing to push notifications:', error);
    }
  };

  const sendSubscriptionToServer = async (subscription: PushSubscription) => {
    try {
      const response = await fetch('/api/push/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          subscription: subscription.toJSON(),
          userId: 'guest' // Replace with actual user ID
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to send subscription to server');
      }
      
      console.log('Subscription sent to server successfully');
    } catch (error) {
      console.error('Error sending subscription to server:', error);
    }
  };

  const showTestNotification = () => {
    if (permission.granted) {
      new Notification('ICFES Leveling', {
        body: '¡Bienvenido a la aventura del conocimiento!',
        icon: '/icons/icon-192x192.png',
        badge: '/icons/battle.png',
        tag: 'welcome',
        requireInteraction: false,
        silent: false
      });
    }
  };

  const openNotificationSettings = () => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.ready.then((registration) => {
        registration.pushManager.getSubscription().then((subscription) => {
          if (subscription) {
            subscription.unsubscribe();
            console.log('Unsubscribed from push notifications');
          }
        });
      });
    }
    setShowSettings(true);
  };

  const getPermissionStatusText = () => {
    if (permission.granted) return 'Permitidas';
    if (permission.denied) return 'Denegadas';
    return 'No configuradas';
  };

  const getPermissionStatusColor = () => {
    if (permission.granted) return 'text-green-400';
    if (permission.denied) return 'text-red-400';
    return 'text-yellow-400';
  };

  const getPermissionStatusIcon = () => {
    if (permission.granted) return <CheckCircle className="w-5 h-5 text-green-400" />;
    if (permission.denied) return <XCircle className="w-5 h-5 text-red-400" />;
    return <AlertTriangle className="w-5 h-5 text-yellow-400" />;
  };

  if (!isSupported) {
    return (
      <div className="bg-yellow-900/20 rounded-lg p-4 border border-yellow-500/30">
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-yellow-400" />
          <div>
            <h3 className="font-semibold text-yellow-400">Notificaciones no soportadas</h3>
            <p className="text-sm text-yellow-300">
              Tu navegador no soporta notificaciones push
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Permission Status */}
      <div className="bg-gray-900/90 rounded-lg p-4 border border-purple-500/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {getPermissionStatusIcon()}
            <div>
              <h3 className="font-semibold text-white">Notificaciones Push</h3>
              <p className={`text-sm ${getPermissionStatusColor()}`}>
                Estado: {getPermissionStatusText()}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {permission.granted ? (
              <Bell className="w-5 h-5 text-green-400" />
            ) : (
              <BellOff className="w-5 h-5 text-gray-400" />
            )}
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        {!permission.granted && !permission.denied && (
          <motion.button
            onClick={requestPermission}
            disabled={isLoading}
            className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-semibold transition-all flex items-center justify-center gap-2"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {isLoading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
            ) : (
              <Bell className="w-4 h-4" />
            )}
            {isLoading ? 'Configurando...' : 'Activar Notificaciones'}
          </motion.button>
        )}

        {permission.granted && (
          <motion.button
            onClick={showTestNotification}
            className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold transition-all flex items-center justify-center gap-2"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Zap className="w-4 h-4" />
            Probar Notificación
          </motion.button>
        )}

        {permission.denied && (
          <motion.button
            onClick={openNotificationSettings}
            className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-all flex items-center justify-center gap-2"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Settings className="w-4 h-4" />
            Configurar Manualmente
          </motion.button>
        )}
      </div>

      {/* Notification Types Info */}
      {permission.granted && (
        <div className="bg-gray-900/90 rounded-lg p-4 border border-purple-500/30">
          <h4 className="font-semibold text-white mb-3">Tipos de Notificaciones</h4>
          <div className="space-y-2 text-sm text-gray-300">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-red-400 rounded-full" />
              <span>Batallas en tiempo real</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-blue-400 rounded-full" />
              <span>Misiones diarias</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-400 rounded-full" />
              <span>Logros desbloqueados</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-purple-400 rounded-full" />
              <span>Actividad de guild</span>
            </div>
          </div>
        </div>
      )}

      {/* Settings Modal */}
      <AnimatePresence>
        {showSettings && (
          <motion.div
            className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="bg-gray-900 rounded-lg p-6 max-w-md w-full border border-purple-500/30"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
            >
              <div className="text-center">
                <Settings className="w-16 h-16 text-blue-400 mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-white mb-4">
                  Configurar Notificaciones
                </h2>
                <p className="text-gray-300 mb-6">
                  Para activar las notificaciones, ve a la configuración de tu navegador y permite las notificaciones para este sitio.
                </p>
                
                <div className="space-y-3 mb-6 text-left">
                  <div className="bg-gray-800/50 rounded-lg p-3">
                    <h3 className="font-semibold text-white mb-2">Chrome/Edge:</h3>
                    <p className="text-sm text-gray-300">
                      Configuración → Privacidad y seguridad → Configuración del sitio → Notificaciones
                    </p>
                  </div>
                  
                  <div className="bg-gray-800/50 rounded-lg p-3">
                    <h3 className="font-semibold text-white mb-2">Firefox:</h3>
                    <p className="text-sm text-gray-300">
                      Configuración → Privacidad y seguridad → Permisos → Notificaciones
                    </p>
                  </div>
                  
                  <div className="bg-gray-800/50 rounded-lg p-3">
                    <h3 className="font-semibold text-white mb-2">Safari:</h3>
                    <p className="text-sm text-gray-300">
                      Preferencias → Sitios web → Notificaciones
                    </p>
                  </div>
                </div>
                
                <button
                  onClick={() => setShowSettings(false)}
                  className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold transition-all"
                >
                  Entendido
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
} 