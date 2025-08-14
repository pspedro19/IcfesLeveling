#!/bin/bash

# ULTRA OPTIMIZED STARTUP SCRIPT FOR NEXT.JS
echo "🚀 Starting ICFES Frontend with ULTRA optimization..."

# Set maximum Node.js memory and performance options
export NODE_OPTIONS="--max-old-space-size=8192 --max-semi-space-size=1024"

# Clear all caches to prevent memory issues
echo "🧹 Clearing caches..."
rm -rf .next
rm -rf node_modules/.cache
rm -rf .swc

# Create optimized directories
mkdir -p .next/cache
mkdir -p .swc

# Set environment for maximum performance
export NEXT_TELEMETRY_DISABLED=1
export NEXT_SHARP_PATH=/app/node_modules/sharp

# Start Next.js with ultra optimization
echo "🎯 Starting Next.js with ULTRA optimization..."
npm run dev -- --hostname 0.0.0.0 --port 4001
