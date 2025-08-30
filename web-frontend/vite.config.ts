import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/flight-search-mcp/',
  server: {
    proxy: {
      '/chat': 'http://localhost:3000',
      '/suggestions': 'http://localhost:3000',
    }
  }
})
