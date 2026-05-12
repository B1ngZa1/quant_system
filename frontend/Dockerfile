# 构建阶段
FROM node:18-alpine as build-stage

WORKDIR /app

# 安装依赖 (不能使用 --only=production，因为需要 vite 和 vue-tsc 来构建)
COPY package.json package-lock.json ./
RUN npm ci

# 复制源码并打包
COPY . .
RUN npm run build

# 生产阶段
FROM nginx:alpine as production-stage

# 将打包好的文件复制到 Nginx 默认目录
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Nginx 配置：Vue Router history 模式 + API 反向代理 + 健康检查
RUN echo 'server { \
    listen       80; \
    server_name  localhost; \
    \
    location /health { \
        access_log off; \
        return 200 "ok"; \
        add_header Content-Type text/plain; \
    } \
    \
    location /api/ { \
        proxy_pass http://backend:8000/api/; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
        proxy_set_header X-Forwarded-Proto $scheme; \
        proxy_connect_timeout 30s; \
        proxy_read_timeout 60s; \
    } \
    \
    location / { \
        root   /usr/share/nginx/html; \
        index  index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
