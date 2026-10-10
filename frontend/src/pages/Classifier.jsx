import { useCallback, useState } from 'react'
import { classifyPassport } from '../api/client'

const ACCEPTED = '.jpg,.jpeg,.png,.webp,.pdf'

export default function Classifier() {
  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleFile = (f) => {
    setFile(f)
    setResult(null)
    setError(null)
  }

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }, [])

  const onDragOver = (e) => { e.preventDefault(); setDragging(true) }
  const onDragLeave = () => setDragging(false)

  const onFileChange = (e) => {
    const f = e.target.files[0]
    if (f) handleFile(f)
  }

  const onSubmit = async (e) => {
    e.preventDefault()
    if (!file) return

    setLoading(true)
    setProgress(0)
    setResult(null)
    setError(null)

    try {
      const data = await classifyPassport(file, setProgress)
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setFile(null)
    setResult(null)
    setError(null)
    setProgress(0)
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4 py-12">
      <div className="w-full max-w-lg">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-slate-800">Passport Expiry Checker</h1>
          <p className="text-slate-500 mt-2 text-sm">
            Upload a passport image to check whether it is expired.
          </p>
        </div>

        {/* Result card */}
        {result && (
          <div
            className={`rounded-2xl p-6 mb-6 shadow-md text-white ${
              result.expired === true
                ? 'bg-red-500'
                : result.expired === false
                ? 'bg-green-500'
                : 'bg-amber-500'
            }`}
          >
            <div className="text-4xl font-extrabold mb-1">
              {result.expired === true ? 'EXPIRED' : result.expired === false ? 'VALID' : 'UNKNOWN'}
            </div>
            <p className="text-white/90 text-sm mb-4">{result.message}</p>
            <div className="grid grid-cols-2 gap-2 text-xs text-white/80">
              <span>Expiry date</span>
              <span className="font-medium text-white">{result.expiry_date ?? '—'}</span>
              <span>MRZ detected</span>
              <span className="font-medium text-white">{result.mrz_detected ? 'Yes' : 'No'}</span>
              <span>Confidence</span>
              <span className="font-medium text-white">{Math.round(result.confidence * 100)}%</span>
              <span>Method</span>
              <span className="font-medium text-white">{result.method}</span>
            </div>
            <button
              onClick={reset}
              className="mt-4 text-xs underline text-white/80 hover:text-white"
            >
              Check another passport
            </button>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="rounded-xl bg-red-100 border border-red-300 text-red-700 px-4 py-3 text-sm mb-6">
            {error}
          </div>
        )}

        {/* Upload form */}
        {!result && (
          <form onSubmit={onSubmit}>
            {/* Drop zone */}
            <label
              onDrop={onDrop}
              onDragOver={onDragOver}
              onDragLeave={onDragLeave}
              className={`flex flex-col items-center justify-center w-full h-52 rounded-2xl border-2 border-dashed cursor-pointer transition-colors ${
                dragging
                  ? 'border-blue-500 bg-blue-50'
                  : file
                  ? 'border-green-400 bg-green-50'
                  : 'border-slate-300 bg-white hover:border-blue-400 hover:bg-blue-50'
              }`}
            >
              <input
                type="file"
                accept={ACCEPTED}
                className="hidden"
                onChange={onFileChange}
              />
              {file ? (
                <>
                  <svg className="w-10 h-10 text-green-500 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <p className="text-sm font-medium text-slate-700">{file.name}</p>
                  <p className="text-xs text-slate-400 mt-1">{(file.size / 1024).toFixed(1)} KB</p>
                </>
              ) : (
                <>
                  <svg className="w-10 h-10 text-slate-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                      d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <p className="text-sm text-slate-500">Drag & drop or <span className="text-blue-600 font-medium">browse</span></p>
                  <p className="text-xs text-slate-400 mt-1">JPG, PNG, WEBP, PDF — max 10 MB</p>
                </>
              )}
            </label>

            {/* Progress bar */}
            {loading && (
              <div className="mt-4 w-full bg-slate-200 rounded-full h-1.5">
                <div
                  className="bg-blue-500 h-1.5 rounded-full transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
            )}

            <button
              type="submit"
              disabled={!file || loading}
              className="mt-4 w-full py-3 rounded-xl bg-blue-600 text-white font-semibold text-sm disabled:opacity-40 hover:bg-blue-700 transition-colors"
            >
              {loading ? 'Analysing…' : 'Check Passport'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
