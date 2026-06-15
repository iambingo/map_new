import tailwindcss from '@tailwindcss/vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';
import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  envDir: './env',
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    hmr: process.env.DISABLE_HMR !== 'true',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          const normalizedId = id.replace(/\\/g, '/');
          if (!normalizedId.includes('node_modules')) return;

          if (normalizedId.includes('/node_modules/@vue/') || normalizedId.includes('/node_modules/vue/')) {
            return 'vendor-vue';
          }
          if (normalizedId.includes('/node_modules/echarts/')) {
            return 'vendor-echarts';
          }
          if (normalizedId.includes('/node_modules/zrender/')) {
            return 'vendor-zrender';
          }
          if (normalizedId.includes('/node_modules/vue-echarts/')) {
            return 'vendor-vue-echarts';
          }
          if (normalizedId.includes('/node_modules/@element-plus/')) {
            return 'vendor-element-icons';
          }
          if (normalizedId.includes('/node_modules/element-plus/')) {
            return 'vendor-element-plus';
          }
          if (normalizedId.includes('/node_modules/axios/')) {
            return 'vendor-axios';
          }
          return 'vendor';
        },
      },
    },
  },
});
