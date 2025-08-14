import { useEffect, useState } from 'react';
// import { useNotifications } from '@/components/ui/EpicNotification'; // Comentado temporalmente
import { Download, CheckCircle, AlertCircle } from 'lucide-react';

export function useServiceWorker() {
  const [isInstalled, setIsInstalled] = useState(false);
  const [isOffline, setIsOffline] = useState(false); // Inicializar como false y actualizar en useEffect
  const [registration, setRegistration] = useState<ServiceWorkerRegistration | null>(null);
  // const { showNotification } = useNotifications(); // Comentado temporalmente
  const showNotification = (options: any) => console.log('Notification:', options); // Mock temporal

  useEffect(() => {
    // Inicializar estado offline después del primer render
    setIsOffline(!navigator.onLine);
    
    // Check if service workers are supported
    if (!('serviceWorker' in navigator)) {
      console.log('Service workers not supported');
      return;
    }

    // Register service worker
    const registerSW = async () => {
      try {
        const reg = await navigator.serviceWorker.register('/sw.js', {
          scope: '/'
        });
        
        setRegistration(reg);
        console.log('Service worker registered:', reg);

        // Check if this is the first install
        reg.addEventListener('updatefound', () => {
          const newWorker = reg.installing;
          
          newWorker?.addEventListener('statechange', () => {
            if (newWorker.state === 'activated') {
              setIsInstalled(true);
              
              // Show install success notification
              showNotification({
                type: 'success',
                title: 'App Instalada',
                message: 'IcfesLeveling está lista para usar offline',
                icon: <Download className="w-6 h-6" />,
                duration: 5000,
              });
            }
          });
        });

        // Check for updates
        reg.addEventListener('controllerchange', () => {
          showNotification({
            type: 'info',
            title: 'Actualización Disponible',
            message: 'La app se actualizará al recargar',
            icon: <CheckCircle className="w-6 h-6" />,
            duration: 5000,
            actions: [{
              label: 'Recargar',
              onClick: () => window.location.reload(),
            }],
          });
        });

      } catch (error) {
        console.error('Service worker registration failed:', error);
      }
    };

    registerSW();

    // Listen for online/offline events
    const handleOnline = () => {
      setIsOffline(false);
      showNotification({
        type: 'success',
        title: 'Conexión Restaurada',
        message: 'El portal ha vuelto a conectarse',
        icon: <CheckCircle className="w-6 h-6" />,
        duration: 3000,
      });
    };

    const handleOffline = () => {
      setIsOffline(true);
      showNotification({
        type: 'warning',
        title: 'Modo Offline',
        message: 'Entrando en modo supervivencia sin conexión',
        icon: <AlertCircle className="w-6 h-6" />,
        duration: 5000,
      });
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [showNotification]);

  // Check for updates manually
  const checkForUpdates = async () => {
    if (registration) {
      try {
        await registration.update();
        console.log('Checked for updates');
      } catch (error) {
        console.error('Update check failed:', error);
      }
    }
  };

  // Request notification permission
  const requestNotificationPermission = async () => {
    if ('Notification' in window && Notification.permission === 'default') {
      const permission = await Notification.requestPermission();
      
      if (permission === 'granted') {
        showNotification({
          type: 'success',
          title: 'Notificaciones Activadas',
          message: 'Recibirás alertas de misiones y eventos',
          duration: 3000,
        });
      }
    }
  };

  return {
    isInstalled,
    isOffline,
    checkForUpdates,
    requestNotificationPermission,
  };
}