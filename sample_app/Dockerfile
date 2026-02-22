# Stage 1: builder
FROM node:20-alpine AS builder

# System setup
RUN addgroup -g 10001 appuser && adduser -u 10001 -G appuser -s /bin/sh -D appuser

# COPY dependency manifests only
WORKDIR /app
COPY backend/package*.json ./

# RUN dependency installation
RUN npm install

# COPY source code
COPY backend/ .

# RUN build command
RUN npm run build

# Stage 2: runtime
FROM node:20-alpine

# System setup
RUN addgroup -g 10001 appuser && adduser -u 10001 -G appuser -s /bin/sh -D appuser

# Set working directory
WORKDIR /app

# Copy build output from builder stage
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules

# Set environment variables
ENV NODE_ENV=production

# Expose port
EXPOSE 3000

# HEALTHCHECK
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD wget -qO- http://localhost:3000/health || exit 1

# Set user
USER appuser

# OCI labels
ARG GIT_COMMIT_SHA
ARG APP_VERSION=1.0.0
ARG BUILD_DATE
LABEL org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.revision="${GIT_COMMIT_SHA}" \
      org.opencontainers.image.created="${BUILD_DATE}"

# CMD
CMD ["node", "dist/index.js"]