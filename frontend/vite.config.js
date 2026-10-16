import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  // Load the root .env (one level up from frontend/)
  const env = loadEnv(mode, '../', '')
  const backendPort = env.PORT || 8888
  const backendUrl = `http://${!env.HOST || env.HOST === '0.0.0.0' ? 'localhost' : env.HOST}:${backendPort}`

  return {
    define: {
      __APP_CONFIG__: JSON.stringify({
        maxUploadMb: Number(env.MAX_UPLOAD_MB || 10),
        acceptedExtensions: env.ALLOWED_UPLOAD_EXTENSIONS || '.jpg,.jpeg,.png,.webp,.pdf',
        requestTimeoutMs: Number(env.REQUEST_TIMEOUT_MS || 600000),
      }),
    },
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
