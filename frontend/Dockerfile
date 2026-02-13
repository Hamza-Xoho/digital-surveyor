# Stage 0, "build-stage", based on Bun, to build and compile the frontend
FROM oven/bun:1 AS build-stage

WORKDIR /app

COPY package.json bun.lock /app/

COPY frontend/package.json /app/frontend/

WORKDIR /app/frontend

# --no-verify: lockfile is generated on macOS (darwin) but Docker builds on
# Linux — platform-specific package tarballs (e.g. @biomejs/cli-linux-arm64
# vs @biomejs/cli-darwin-arm64) have different hashes, so integrity checks
# for cross-platform packages will fail without this flag.
RUN bun install --no-verify

COPY ./frontend /app/frontend
ARG VITE_API_URL

RUN bun run build


# Stage 1, based on Nginx, to have only the compiled app, ready for production with Nginx
FROM nginx:1

COPY --from=build-stage /app/frontend/dist/ /usr/share/nginx/html

COPY ./frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY ./frontend/nginx-backend-not-found.conf /etc/nginx/extra-conf.d/backend-not-found.conf
