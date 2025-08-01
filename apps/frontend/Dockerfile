FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source code
COPY . .

# Build the application
ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run build

# Expose port
EXPOSE 4001

# Set environment variables
ENV PORT 4001
ENV HOSTNAME "0.0.0.0"
ENV NODE_ENV production

# Start the application
CMD ["npm", "start"] 