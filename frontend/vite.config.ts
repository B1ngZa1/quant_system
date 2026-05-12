import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { fileURLToPath, URL } from 'node:url'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import viteCompression from 'vite-plugin-compression'
import { visualizer } from 'rollup-plugin-visualizer'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [
    vue(),
    AutoImport({
      imports: ['vue', 'vue-router', 'pinia'],
      resolvers: [ElementPlusResolver()],
      dts: 'src/auto-imports.d.ts'
    }),
    Components({
      resolvers: [
        ElementPlusResolver({
          importStyle: 'sass'
        })
      ],
      dts: 'src/components.d.ts'
    }),
    mode === 'production'
      ? viteCompression({ algorithm: 'gzip', ext: '.gz' })
      : null
  ],
  test: {
    environment: 'jsdom',
    include: ['src/**/*.spec.ts'],
    globals: false
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '~': fileURLToPath(new URL('./src/assets', import.meta.url))
    },
    // 优化模块解析
    dedupe: ['vue', 'element-plus', 'echarts']
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api'),
        timeout: 60000,
        proxyTimeout: 60000
      }
    },
    cors: true,
    hmr: {
      overlay: false
    },
    // 优化预构建
    preTransformRequests: true
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: mode === 'development',
    // 启用CSS代码分割
    cssCodeSplit: true,
    // 默认 esbuild 压缩，无需额外依赖
    minify: 'esbuild',
    esbuild: {
      drop: mode === 'production' ? ['console', 'debugger'] : []
    },
    rollupOptions: {
      plugins: mode === 'analyze' ? [visualizer({ filename: 'dist/stats.html', gzipSize: true })] : [],
      output: {
        // 更细粒度代码分割：进一步降低首屏加载体积
        manualChunks(id) {
          if (!id.includes('node_modules')) return
          if (id.includes('echarts')) return 'vendor-echarts'
          if (id.includes('element-plus')) return 'vendor-element'
          if (id.includes('@element-plus/icons-vue')) return 'vendor-icons'
          if (id.includes('vue-router')) return 'vendor-router'
          if (id.includes('pinia')) return 'vendor-store'
          if (id.includes('vue')) return 'vendor-vue'
          if (id.includes('axios')) return 'vendor-axios'
          if (id.includes('dayjs')) return 'vendor-dayjs'
          return 'vendor-misc'
        },
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name || ''
          if (info.endsWith('.css')) {
            return 'css/[name]-[hash][extname]'
          }
          if (/\.(png|jpe?g|gif|svg|webp|ico)$/.test(info)) {
            return 'images/[name]-[hash][extname]'
          }
          if (/\.(woff2?|ttf|otf|eot)$/.test(info)) {
            return 'fonts/[name]-[hash][extname]'
          }
          return 'assets/[name]-[hash][extname]'
        }
      }
    },
    // 启用构建缓存
    reportCompressedSize: false,
    chunkSizeWarningLimit: 1000
  },
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@use "@/styles/variables.scss" as *;`,
        charset: false
      }
    },
    // 优化CSS处理
    devSourcemap: true
  },
  // 优化依赖预构建
  optimizeDeps: {
    include: [
      'vue',
      'vue-router',
      'pinia',
      'element-plus',
      'axios',
      'dayjs'
    ],
    exclude: ['echarts']
  }
}))
