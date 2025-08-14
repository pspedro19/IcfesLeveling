'use client';

import { useEffect } from 'react';
import { useServiceWorker } from '@/hooks/useServiceWorker';

export default function ServiceWorkerRegistration() {
  const { requestNotificationPermission } = useServiceWorker();

  useEffect(() => {
    // Request notification permission after a delay
    const timer = setTimeout(() => {
      requestNotificationPermission();
    }, 10000); // 10 seconds after page load

    return () => clearTimeout(timer);
  }, [requestNotificationPermission]);

  return null; // This component doesn't render anything
}