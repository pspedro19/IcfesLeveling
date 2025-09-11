'use client';

import { useEffect } from 'react';

export function HydrationProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Hydrate the store after mount
    const authStore = require('@/stores/useAuthStore').useAuthStore;
    if (authStore?.persist?.rehydrate) {
      authStore.persist.rehydrate();
    }
  }, []);

  return <>{children}</>;
}