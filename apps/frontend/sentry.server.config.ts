// This file configures the initialization of Sentry for the server.
// The config you add here will be used whenever the server handles a request.
// https://docs.sentry.io/platforms/javascript/guides/nextjs/

import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.SENTRY_DSN || process.env.NEXT_PUBLIC_SENTRY_DSN,

  // Adjust this value in production, or use tracesSampler for greater control
  tracesSampleRate: 1,

  // Setting this option to true will print useful information to the console while you're setting up Sentry.
  debug: false,

  // Uncomment the line below to enable Spotlight (https://spotlightjs.com)
  // spotlight: process.env.NODE_ENV === 'development',

  // Performance Monitoring
  tracePropagationTargets: [
    "localhost",
    process.env.NEXT_PUBLIC_API_URL || "",
    /^https:\/\/yourserver\.io\/api/,
  ],

  // Additional options
  environment: process.env.NODE_ENV,
  
  beforeSend(event, hint) {
    // Filter out specific errors
    if (event.exception) {
      const error = hint.originalException;
      
      // Don't send cancelled requests
      if (error?.message?.includes('cancelled')) {
        return null;
      }
    }
    
    return event;
  },
});