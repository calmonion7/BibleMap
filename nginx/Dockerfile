# 빌드 컨텍스트 = 레포 루트(compose) — 프론트 빌드와 nginx.conf 를 이미지에 굽는다(롤백 때 함께 되돌아간다).
FROM node:24-alpine AS build
WORKDIR /src
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --silent
COPY frontend/ ./
RUN npm run build --silent

FROM nginx:alpine
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY --from=build /src/dist /usr/share/nginx/html
