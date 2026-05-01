# ── Frontend Dockerfile ────────────────────────────────
# Multi-stage build for Next.js standalone output

# Stage 1: Install dependencies
FROM node:20-alpine AS deps
# Install python and build tools needed for native web3 modules (like bufferutil and usb)
RUN apk add --no-cache python3 make g++ linux-headers eudev-dev libusb-dev
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --legacy-peer-deps

# Stage 2: Build the application
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ ./

# Build-time env vars (will be baked into the bundle)
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

# Stage 3: Production runner
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV HOSTNAME="0.0.0.0"
# Azure Container Apps uses port 3000
ENV PORT=3000

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy standalone output from builder (includes everything needed including node_modules)
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000

# Start the Next.js server  
# The PORT environment variable tells Next.js which port to listen on
CMD ["node", "server.js"]
