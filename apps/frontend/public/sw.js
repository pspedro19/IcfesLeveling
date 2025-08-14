// Service Worker para ICFES Leveling PWA
const CACHE_NAME = 'icfes-leveling-v1';
const STATIC_CACHE = 'icfes-static-v1';
const DYNAMIC_CACHE = 'icfes-dynamic-v1';

// Archivos a cachear estáticamente
const STATIC_FILES = [
  '/',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
  '/icons/battle.png',
  '/icons/quest.png',
  '/favicon.ico'
];

// Instalación del Service Worker
self.addEventListener('install', (event) => {
  console.log('Service Worker: Installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('Service Worker: Caching static files');
        return cache.addAll(STATIC_FILES);
      })
      .then(() => {
        console.log('Service Worker: Static files cached');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('Service Worker: Error caching static files:', error);
      })
  );
});

// Activación del Service Worker
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
              console.log('Service Worker: Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker: Activated');
        return self.clients.claim();
      })
  );
});

// Interceptar requests de red
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Estrategia de cache: Network First para API calls, Cache First para assets
  if (url.pathname.startsWith('/api/')) {
    // API calls: Network First
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Cache successful responses
          if (response.status === 200) {
            const responseClone = response.clone();
            caches.open(DYNAMIC_CACHE)
              .then((cache) => {
                cache.put(request, responseClone);
              });
          }
          return response;
        })
        .catch(() => {
          // Fallback to cache if network fails
          return caches.match(request);
        })
    );
  } else if (request.destination === 'image' || request.destination === 'font') {
    // Assets: Cache First
    event.respondWith(
      caches.match(request)
        .then((response) => {
          if (response) {
            return response;
          }
          return fetch(request)
            .then((response) => {
              if (response.status === 200) {
                const responseClone = response.clone();
                caches.open(DYNAMIC_CACHE)
                  .then((cache) => {
                    cache.put(request, responseClone);
                  });
              }
              return response;
            });
        })
    );
  } else {
    // Default: Network First
    event.respondWith(
      fetch(request)
        .catch(() => {
          return caches.match(request);
        })
    );
  }
});

// Manejo de notificaciones push
self.addEventListener('push', (event) => {
  console.log('Service Worker: Push event received');
  
  let notificationData = {
    title: 'ICFES Leveling',
    body: '¡Nueva actividad disponible!',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/battle.png',
    tag: 'default',
    requireInteraction: false,
    silent: false,
    data: {}
  };

  // Si hay datos en el push event, usarlos
  if (event.data) {
    try {
      const pushData = event.data.json();
      notificationData = {
        ...notificationData,
        ...pushData
      };
    } catch (error) {
      console.error('Service Worker: Error parsing push data:', error);
    }
  }

  event.waitUntil(
    self.registration.showNotification(notificationData.title, notificationData)
  );
});

// Manejo de clics en notificaciones
self.addEventListener('notificationclick', (event) => {
  console.log('Service Worker: Notification clicked');
  
  event.notification.close();

  const notificationData = event.notification.data || {};
  let urlToOpen = '/';

  // Determinar URL basada en el tipo de notificación
  switch (notificationData.type) {
    case 'battle':
      urlToOpen = '/battle';
      break;
    case 'quest':
      urlToOpen = '/daily-quests';
      break;
    case 'achievement':
      urlToOpen = '/achievements';
      break;
    case 'guild':
      urlToOpen = '/guilds';
      break;
    default:
      urlToOpen = '/';
  }

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Buscar una ventana abierta
        for (const client of clientList) {
          if (client.url.includes(urlToOpen) && 'focus' in client) {
            return client.focus();
          }
        }
        
        // Si no hay ventana abierta, abrir una nueva
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});

// Manejo de cierre de notificaciones
self.addEventListener('notificationclose', (event) => {
  console.log('Service Worker: Notification closed');
  
  // Aquí puedes enviar analytics sobre el cierre de notificaciones
  const notificationData = event.notification.data || {};
  
  // Enviar evento de analytics si es necesario
  if (notificationData.analytics) {
    // Implementar tracking de analytics
    console.log('Service Worker: Analytics event - notification closed');
  }
});

// Background sync para datos offline
self.addEventListener('sync', (event) => {
  console.log('Service Worker: Background sync event:', event.tag);
  
  if (event.tag === 'background-sync') {
    event.waitUntil(
      // Sincronizar datos offline
      syncOfflineData()
    );
  }
});

// Función para sincronizar datos offline
async function syncOfflineData() {
  try {
    // Obtener datos offline del IndexedDB
    const offlineData = await getOfflineData();
    
    if (offlineData.length > 0) {
      console.log('Service Worker: Syncing offline data:', offlineData.length, 'items');
      
      // Enviar datos al servidor
      for (const data of offlineData) {
        try {
          const response = await fetch(data.url, {
            method: data.method,
            headers: data.headers,
            body: data.body
          });
          
          if (response.ok) {
            // Remover del cache offline si se sincronizó exitosamente
            await removeOfflineData(data.id);
          }
        } catch (error) {
          console.error('Service Worker: Error syncing data:', error);
        }
      }
    }
  } catch (error) {
    console.error('Service Worker: Error in background sync:', error);
  }
}

// Funciones auxiliares para manejo de datos offline
async function getOfflineData() {
  // Implementar lógica para obtener datos del IndexedDB
  return [];
}

async function removeOfflineData(id) {
  // Implementar lógica para remover datos del IndexedDB
  console.log('Service Worker: Removing offline data:', id);
}

// Manejo de errores del Service Worker
self.addEventListener('error', (event) => {
  console.error('Service Worker: Error:', event.error);
});

self.addEventListener('unhandledrejection', (event) => {
  console.error('Service Worker: Unhandled rejection:', event.reason);
});

// Mensajes del Service Worker
self.addEventListener('message', (event) => {
  console.log('Service Worker: Message received:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'GET_VERSION') {
    event.ports[0].postMessage({ version: CACHE_NAME });
  }
});

console.log('Service Worker: Loaded successfully');