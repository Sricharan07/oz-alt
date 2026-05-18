FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ARG VITE_API_URL=""
ARG VITE_DOCS_URL="https://tryoz.dev"
ARG VITE_ADMIN_URL="https://admin.tryoz.dev/admin"
RUN set -eu; \
    export VITE_API_URL="$VITE_API_URL"; \
    export VITE_DOCS_URL="$VITE_DOCS_URL"; \
    export VITE_ADMIN_URL="$VITE_ADMIN_URL"; \
    npm run build

FROM nginx:1.27-alpine

ENV OZ_CONSOLE_API_BASE_URL= \
    OZ_DOCS_URL=https://tryoz.dev \
    OZ_ADMIN_URL=https://admin.tryoz.dev/admin

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.d/40-runtime-config.sh /docker-entrypoint.d/40-runtime-config.sh
COPY --from=build /app/dist /usr/share/nginx/html
RUN chmod +x /docker-entrypoint.d/40-runtime-config.sh

EXPOSE 80
