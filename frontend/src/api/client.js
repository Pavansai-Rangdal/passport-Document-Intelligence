import axios from 'axios'

// Proxy in vite.config.js routes /api and /health to localhost:8000
const api = axios.create({
  baseURL: '/',
  timeout: 60000,
  headers: { Accept: 'application/json' },
})

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred'
    return Promise.reject(new Error(message))
  },
)

export async function getHealth() {
  return api.get('/health')
}

/**
 * Upload a passport image and get an expiry classification.
 * @param {File} file
 * @param {function} onProgress  optional (percent: number) => void
 */
export async function classifyPassport(file, onProgress = null) {
  const formData = new FormData()
  formData.append('file', file)

  return api.post('/api/v1/classify', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onProgress
      ? (evt) => {
          if (evt.total) onProgress(Math.round((evt.loaded * 100) / evt.total))
        }
      : undefined,
  })
}
