# Multi-stage build for optimization
FROM node:18-alpine AS deps
WORKDIR /app

# Copy package files first for better caching
COPY package.json package-lock.json* ./
RUN npm ci --only=production --legacy-peer-deps && npm cache clean --force

# Build stage
FROM node:18-alpine AS builder
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./
RUN npm ci --legacy-peer-deps

# Copy source code (only what's needed)
COPY public/ ./public/
COPY app/ ./app/
COPY next.config.js ./
COPY tailwind.config.js ./
COPY tsconfig.json ./
COPY postcss.config.js ./
COPY middleware.ts ./
COPY style-dictionary.config.js ./

# Build the application (skip style-dictionary for now)
RUN npx next build

# Production stage
FROM node:18-alpine AS runner
WORKDIR /app

# Set environment variables
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=4001
ENV HOSTNAME=0.0.0.0

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built application
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 4001

# Start the application
CMD ["node", "server.js"] 