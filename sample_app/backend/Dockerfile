# syntax=docker/dockerfile:1

# Using Node.js 20-alpine as the base image for the builder stage
FROM node:20-alpine AS builder

# Set working directory to /app
WORKDIR /app

# Copy package.json and package-lock.json to install dependencies
COPY package*.json ./

# Install dependencies
RUN npm ci --ignore-scripts && npm cache clean --force

# Copy application source code
COPY . .

# Build the application (assuming a Node.js application)
RUN npm run build

# Create a non-root user
RUN addgroup -g 10001 -S appgroup && \
    adduser -u 10001 -S appuser -G appgroup

# Change ownership of the application directory
RUN chown -R appuser:appgroup /app

# Stage 2: Runtime environment
FROM node:20-alpine

# Set working directory to /app
WORKDIR /app

# Copy the pre-built application from the builder stage
COPY --from=builder --chown=appuser:appgroup /app/dist /app/dist
COPY --from=builder --chown=appuser:appgroup /app/package*.json ./

# Install only production dependencies
RUN npm ci --omit=dev --ignore-scripts && npm cache clean --force

# Set the non-root user
USER appuser

# Expose the port the application listens on (assuming port 3000)
EXPOSE 3000

# Use exec form for CMD
CMD ["node", "dist/index.js"]

# Add OCI standard labels
ARG GIT_COMMIT_SHA
ARG APP_VERSION=1.0.0
ARG BUILD_DATE

LABEL org.opencontainers.image.authors="your@email.com" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.revision="${GIT_COMMIT_SHA}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.source="https://github.com/org/repo" \
      org.opencontainers.image.description="Short description"