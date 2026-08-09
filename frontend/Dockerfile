# Two-stage build: compile the SPA with Node, serve the static output with nginx.
# The runtime image carries no Node and no node_modules — only the built assets.

# ---------- build ----------
FROM node:20-alpine AS build
WORKDIR /app

# Copy manifests first so the dependency layer is cached and only reinstalls
# when package.json / package-lock.json actually change.
COPY package*.json ./
RUN npm ci

COPY . .

# VITE_* vars are inlined into the bundle at BUILD time, not read at runtime.
# Anything baked in here is visible to anyone who opens devtools — never put a
# secret in a VITE_ variable.
#
# Left empty by default so the app calls a relative /api, which nginx proxies.
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# ---------- serve ----------
FROM nginx:alpine

# nginx.conf is a template: BACKEND_ORIGIN is substituted at container start,
# so one image can be pointed at a different backend without rebuilding.
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

ENV BACKEND_ORIGIN=http://fishclaim_backend:8000

EXPOSE 80
