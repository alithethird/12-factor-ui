# syntax=docker/dockerfile:experimental

# ... (Build stages 1 and 2 are the same)
FROM oven/bun:latest AS dependencies
WORKDIR /srv
ARG BUILD_ENV=production
COPY app/package.json app/bun.lock ./
RUN --mount=type=cache,target=/usr/local/share/.cache/bun \
  if [ "$BUILD_ENV" = "development" ]; then \
    bun install; \
  else \
    bun install --production; \
  fi
FROM dependencies AS build
COPY app/index.html app/tsconfig.json app/vite.config.ts ./
COPY app/src ./src
RUN bun run build

# --- FINAL IMAGE ---
FROM ubuntu:22.04
ARG HOST=0.0.0.0
ARG PORT=80
ARG BUILD_ENV=production
ENV PORT=$PORT
ENV HOST=$HOST
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /srv

# 1. Install dependencies
RUN apt-get update && apt-get install -y \
    snapd \
    git \
    unzip \
    tar \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Node.js 22
RUN curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
RUN echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list
RUN apt-get update && apt-get install -y nodejs

# 3. Copy the entrypoint script
COPY entrypoint.sh /srv/entrypoint.sh
RUN chmod +x /srv/entrypoint.sh

# Install nodemon and bun globally only in development environment
RUN if [ "$BUILD_ENV" = "development" ]; then \
    npm install -g nodemon bun; \
  fi

# 4. Copy the built application
COPY --from=build /srv/node_modules ./node_modules
COPY --from=build /srv/package.json ./package.json
COPY --from=build /srv/bun.lock ./bun.lock
COPY --from=build /srv/dist ./dist

# --- THIS IS THE FIX ---
# 5. Add snap's bin directory to the global PATH
ENV PATH="${PATH}:/snap/bin"
# --- END FIX ---

# 6. Set the entrypoint
ENTRYPOINT ["/srv/entrypoint.sh"]