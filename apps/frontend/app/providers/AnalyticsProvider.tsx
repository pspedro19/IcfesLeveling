'use client';

import { useEffect } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';
import { analytics, trackPageView } from '../lib/analytics';
import { useAuthStore } from '../stores/useAuthStore';

interface AnalyticsProviderProps {
  children: React.ReactNode;
}

export default function AnalyticsProvider({ children }: AnalyticsProviderProps) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { user } = useAuthStore();
  
  // Initialize analytics
  useEffect(() => {
    const measurementId = process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID;
    if (measurementId) {
      analytics.initialize(measurementId);
    }
  }, []);
  
  // Track page views on route changes
  useEffect(() => {
    const url = pathname + (searchParams?.toString() ? `?${searchParams}` : '');
    trackPageView(url);
  }, [pathname, searchParams]);
  
  // Update user properties when user changes
  useEffect(() => {
    if (user) {
      analytics.setUserProperties({
        userId: user.id,
        userLevel: user.level,
        userRank: user.rank,
        isPremium: user.is_premium,
      });
    }
  }, [user]);
  
  return <>{children}</>;
}