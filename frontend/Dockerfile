# ─── Stage 1: Build ───────────────────────────────────────────────────────────
FROM node:22-alpine AS builder
WORKDIR /app

# Enable corepack (pnpm)
RUN corepack enable && corepack prepare pnpm@latest --activate

# Install deps first (better layer caching)
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml* ./
RUN pnpm install --frozen-lockfile

# Build-time env vars (injected by Dokploy at build time)
ARG PUBLIC_API_URL=http://localhost:8000
ARG PUBLIC_SITE_URL=http://localhost:4321
ARG PUBLIC_PB_URL=http://localhost:8090
ENV PUBLIC_API_URL=$PUBLIC_API_URL
ENV PUBLIC_SITE_URL=$PUBLIC_SITE_URL
ENV PUBLIC_PB_URL=$PUBLIC_PB_URL

# Copy source and build
COPY . .
RUN pnpm run build

# ─── Stage 2: Serve static files with Nginx ───────────────────────────────────
FROM nginx:1.27-alpine AS runner
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
