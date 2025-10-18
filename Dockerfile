# syntax=docker/dockerfile:experimental

# Build stage: Install dependencies
# ===
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

# Build stage: Run "bun build"
# ===
FROM dependencies AS build
COPY app/index.html app/tsconfig.json app/vite.config.ts ./
COPY app/src ./src
RUN bun run build

# Build the demo image
FROM node:22

ARG HOST=0.0.0.0
ARG PORT=80
ARG BUILD_ENV=production

ENV PORT=$PORT
ENV HOST=$HOST

WORKDIR /srv

# Install nodemon and bun globally only in development environment
RUN if [ "$BUILD_ENV" = "development" ]; then \
    npm install -g nodemon bun; \
  fi

# Import code, build assets
COPY --from=build /srv/node_modules ./node_modules
COPY --from=build /srv/package.json ./package.json
COPY --from=build /srv/bun.lock ./bun.lock
COPY --from=build /srv/dist ./dist

CMD ["node", "dist/server/server.js"]
