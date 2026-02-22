# Stage 1: Builder
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Set non-root user
RUN addgroup -g 10001 appuser && adduser -u 10001 -G appuser -s /bin/sh -D appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Install dependencies and copy source code
COPY backend/package*.json ./
RUN npm ci
COPY backend/ .
RUN npm run build

# Stage 2: Runtime
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Set non-root user
RUN addgroup -g 10001 appuser && adduser -u 10001 -G appuser -s /bin/sh -D appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Copy build output from builder stage
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package*.json ./

# Expose port
EXPOSE 3000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD wget -qO- http://localhost:3000/health || exit 1

# Set environment variables
ENV NODE_ENV=production

# Set command to run
CMD ["node", "index.js"]

# OCI labels
ARG GIT_COMMIT_SHA
ARG APP_VERSION=1.0.0
ARG BUILD_DATE
LABEL org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.revision="${GIT_COMMIT_SHA}" \
      org.opencontainers.image.created="${BUILD_DATE}"