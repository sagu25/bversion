import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      },
      '/reset': { target: 'http://localhost:8000', changeOrigin: true },
      '/approve': { target: 'http://localhost:8000', changeOrigin: true },
      '/deny': { target: 'http://localhost:8000', changeOrigin: true },
      '/agent': { target: 'http://localhost:8000', changeOrigin: true },
      '/logs': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})
