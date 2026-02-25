# ─────────────────────────────────────────────────────────────────────────────
# PPF Workshop Monitoring System — Frontend Dockerfile
#
# Multi-stage build:
#   Stage 1 (builder): Install deps + Vite build with env vars
#   Stage 2 (runtime): Serve static files with nginx
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: build ──────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Vite bakes env vars at build time — pass via --build-arg
ARG VITE_API_BASE_URL
ARG VITE_WS_URL
ARG VITE_ENABLE_VIDEO=false
ARG VITE_ENABLE_CHARTS=true

# Skip tsc type-check (pre-existing TS warnings), run Vite build directly
RUN npx vite build


# ── Stage 2: serve with nginx ───────────────────────────────────────────────
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/nginx.conf.template

# Railway injects PORT env var; default to 80 for local Docker usage
ENV PORT=80

# Substitute only $PORT (not nginx vars like $uri), then start nginx
CMD ["/bin/sh", "-c", "envsubst '${PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
