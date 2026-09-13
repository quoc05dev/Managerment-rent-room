# ===== BUILD STAGE =====
FROM node:18-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* .npmrc ./
RUN npm ci
COPY . .
RUN npm run build

# ===== SERVE STAGE =====
FROM nginx:alpine
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
