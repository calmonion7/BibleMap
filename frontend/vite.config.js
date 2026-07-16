import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // 빌드 식별자 — 배포마다 바뀌어 API 응답 캐시(max-age=3600)를 배포 시 무력화(api.js).
  define: {
    __BUILD_ID__: JSON.stringify(String(Date.now())),
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('maplibre-gl')) return 'maplibre'
            return 'vendor'
          }
        },
      },
    },
  },
})
