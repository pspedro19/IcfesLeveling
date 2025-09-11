/**
 * Sentry Client Configuration
 * Production monitoring and error tracking
 */

import * as Sentry from '@sentry/nextjs';

const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN;
const environment = process.env.NEXT_PUBLIC_ENVIRONMENT || 'development';
const isProduction = environment === 'production';

Sentry.init({
  dsn: SENTRY_DSN,
  environment,
  enabled: isProduction,
  tracesSampleRate: isProduction ? 0.1 : 1.0,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
  release: process.env.NEXT_PUBLIC_APP_VERSION,
  
  ignoreErrors: [
    'ResizeObserver loop limit exceeded',
    'Non-Error promise rejection captured',
    'NetworkError',
    'Network request failed',
    'Failed to fetch',
    'AbortError',
    'Script error'
  ],
  
  beforeTransaction(transaction) {
    if (transaction.name === 'GET /health') return null;
    if (transaction.name?.includes('/_next/')) return null;
    return transaction;
  },
  
  integrations: [
    new Sentry.BrowserTracing({
      routingInstrumentation: Sentry.nextRouterInstrumentation,
      tracingOrigins: ['localhost', 'icfesleveling.com', /^\//]
    }),
    new Sentry.Replay({
      maskAllText: false,
      maskAllInputs: true,
      blockAllMedia: false
    })
  ],
  
  debug: !isProduction,
  attachStacktrace: true,
  autoSessionTracking: true,
  maxBreadcrumbs: 50
});

export function setSentryUser(user: any) {
  Sentry.setUser(user);
}

export function clearSentryUser() {
  Sentry.setUser(null);
}

export function captureError(error: Error, context?: any) {
  Sentry.withScope((scope) => {
    if (context) scope.setContext('additional', context);
    Sentry.captureException(error);
  });
}