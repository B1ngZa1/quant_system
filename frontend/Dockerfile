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

# 如果需要支持 Vue Router 的 history 模式，可以替换默认配置
RUN echo 'server { \
    listen       80; \
    server_name  localhost; \
    location / { \
        root   /usr/share/nginx/html; \
        index  index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]