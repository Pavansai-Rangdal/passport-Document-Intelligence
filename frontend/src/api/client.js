import axios from 'axios'
import { requestTimeoutMs } from '../config'

// Proxy in vite.config.js routes /api and /health to the backend (see .env PORT)
const api = axios.create({
  baseURL: '/',
  timeout: requestTimeoutMs,
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
 * Upload passport images and get expiry classifications.
 * @param {File[]} files
 * @param {function} onProgress  optional (percent: number) => void
 */
export async function classifyPassport(files, onProgress = null) {
  const formData = new FormData()
  files.forEach(file => {
    formData.append('files', file)
  })

  return api.post('/api/v1/classify', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onProgress
      ? (evt) => {
          if (evt.total) onProgress(Math.round((evt.loaded * 100) / evt.total))
        }
      : undefined,
  })
}

/**
 * Upload passport files and receive each result as soon as it is ready (NDJSON stream).
 * @param {File[]} files
 * @param {function} onResult  called with each result object, in upload order
 */
export async function classifyPassportStream(files, onResult) {
  const formData = new FormData()
  files.forEach(file => formData.append('files', file))

  const res = await fetch('/api/v1/classify/stream', { method: 'POST', body: formData })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed (${res.status})`)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { done, value } = await reader.read()
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done })
    const lines = buffer.split('\n')
    buffer = lines.pop()
    lines.filter(Boolean).forEach(line => onResult(JSON.parse(line)))
    if (done) break
  }
  if (buffer.trim()) onResult(JSON.parse(buffer))
}
