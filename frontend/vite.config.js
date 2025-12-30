import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ command }) => ({
  plugins: [react()],
  base: command === 'build' ? '/static/' : '/',
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
      '/admin': 'http://localhost:8000',
    },
  },
}))
