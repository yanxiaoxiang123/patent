import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
      imports: ['vue', 'vue-router', 'pinia'],
      dts: true
    }),
    Components({
      resolvers: [ElementPlusResolver()],
      dts: true
    })
  ],
  publicDir: fileURLToPath(new URL('../pic', import.meta.url)),
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api/ai': {
        target: 'http://127.0.0.1:8006',
        changeOrigin: true,
        secure: false,
        configure: (proxy, options) => {
          proxy.on('error', () => { });
        }
      },
      '/api/documents': {
        target: 'http://127.0.0.1:8006',
        changeOrigin: true,
        secure: false
      },
      '/api/admin': {
        target: 'http://127.0.0.1:8006',
        changeOrigin: true,
        secure: false
      },
      '/api/auth': {
        target: 'http://127.0.0.1:8006',
        changeOrigin: true,
        secure: false
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia'],
          element: ['element-plus']
        }
      }
    }
  }
})
