import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  // Load the root .env (one level up from frontend/)
  const env = loadEnv(mode, '../', '')
  const backendPort = env.PORT || 8000
  const backendUrl = `http://${env.HOST || 'localhost'}:${backendPort}`

  return {
    plugins: [react()],
    server: {
      port: parseInt(env.FRONTEND_PORT || '3000'),
      proxy: {
        '/api': { target: backendUrl, changeOrigin: true },
        '/health': { target: backendUrl, changeOrigin: true },
      },
    },
  }
})
