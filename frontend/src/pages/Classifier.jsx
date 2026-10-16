import { useCallback, useState } from 'react'
import { classifyPassportStream } from '../api/client'
import { acceptedExtensions as ACCEPTED, maxUploadMb } from '../config'

export default function Classifier() {
  const [files, setFiles] = useState([])
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState([])
  const [error, setError] = useState(null)

  const handleFiles = (fileList) => {
    const all = Array.from(fileList)
    const allowed = ACCEPTED.split(',')
    const maxBytes = maxUploadMb * 1024 * 1024
    const validFiles = all.filter(f =>
      allowed.includes('.' + f.name.split('.').pop().toLowerCase()) && f.size <= maxBytes)
    const skipped = all.filter(f => !validFiles.includes(f)).map(f => f.name)
    setFiles(validFiles)
    setResults([])
    setError(skipped.length
      ? `Skipped ${skipped.length} file(s) (unsupported type or over ${maxUploadMb} MB): ${skipped.join(', ')}`
      : null)
  }

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    const fileList = e.dataTransfer.files
    if (fileList.length > 0) handleFiles(fileList)
  }, [])

  const onDragOver = (e) => { e.preventDefault(); setDragging(true) }
  const onDragLeave = () => setDragging(false)

  const onFileChange = (e) => {
    const fileList = e.target.files
    if (fileList.length > 0) handleFiles(fileList)
  }

  const onSubmit = async (e) => {
    e.preventDefault()
    if (files.length === 0) return

    setLoading(true)
    setResults([])
    setError(null)

    try {
      await classifyPassportStream(files, (r) => setResults(prev => [...prev, r]))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setFiles([])
    setResults([])
    setError(null)
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen px-4 py-12">
      <div className="w-full max-w-lg">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-slate-800">Passport Expiry Checker</h1>
          <p className="text-slate-500 mt-2 text-sm">
            Upload passport images or PDFs to check whether they are expired.
          </p>
        </div>

        {/* Result cards */}
        {(results.length > 0 || loading) && (
          <div className="space-y-4 mb-6">
            {results.map((result, index) => (
              <div
                key={index}
                className={`rounded-2xl p-6 shadow-md text-white ${
                  result.expired === true
                    ? 'bg-red-500'
                    : result.expired === false
                    ? 'bg-green-500'
                    : 'bg-amber-500'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="text-2xl font-extrabold">
                    {result.expired === true ? 'EXPIRED' : result.expired === false ? 'VALID' : 'UNKNOWN'}
                  </div>
                  <div className="text-xs text-white/70 bg-white/20 px-2 py-1 rounded">
                    {result.filename || `File ${index + 1}`}
                  </div>
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
              </div>
            ))}
            {loading && files.slice(results.length).map((f, i) => (
              <div key={`pending-${i}`} className="rounded-2xl p-6 bg-slate-200 text-slate-600 animate-pulse">
                <div className="text-sm font-semibold">Analysing {f.name}…</div>
                <p className="text-xs mt-1">{i === 0 ? 'In progress' : 'Waiting'}</p>
              </div>
            ))}
            {!loading && <button
              onClick={reset}
              className="w-full mt-4 py-2 rounded-xl bg-slate-700 text-white font-semibold text-sm hover:bg-slate-800 transition-colors"
            >
              Check more passports
            </button>}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="rounded-xl bg-red-100 border border-red-300 text-red-700 px-4 py-3 text-sm mb-6">
            {error}
          </div>
        )}

        {/* Upload form */}
        {results.length === 0 && !loading && (
          <form onSubmit={onSubmit}>
            {/* Drop zone */}
            <label
              onDrop={onDrop}
              onDragOver={onDragOver}
              onDragLeave={onDragLeave}
              className={`flex flex-col items-center justify-center w-full h-52 rounded-2xl border-2 border-dashed cursor-pointer transition-colors ${
                dragging
                  ? 'border-blue-500 bg-blue-50'
                  : files.length > 0
                  ? 'border-green-400 bg-green-50'
                  : 'border-slate-300 bg-white hover:border-blue-400 hover:bg-blue-50'
              }`}
            >
              <input
                type="file"
                accept={ACCEPTED}
                multiple
                className="hidden"
                onChange={onFileChange}
              />
              {files.length > 0 ? (
                <>
                  <svg className="w-10 h-10 text-green-500 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <p className="text-sm font-medium text-slate-700">{files.length} file{files.length > 1 ? 's' : ''} selected</p>
                  <p className="text-xs text-slate-400 mt-1">
                    {files.map(f => f.name).join(', ')}
                  </p>
                </>
              ) : (
                <>
                  <svg className="w-10 h-10 text-slate-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                      d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <p className="text-sm text-slate-500">Drag & drop or <span className="text-blue-600 font-medium">browse</span></p>
                  <p className="text-xs text-slate-400 mt-1">{ACCEPTED.split(',').map(e => e.slice(1).toUpperCase()).join(', ')} — max {maxUploadMb} MB each</p>
                </>
              )}
            </label>

            <button
              type="submit"
              disabled={files.length === 0 || loading}
              className="mt-4 w-full py-3 rounded-xl bg-blue-600 text-white font-semibold text-sm disabled:opacity-40 hover:bg-blue-700 transition-colors"
            >
              {loading ? 'Analysing…' : `Check ${files.length} Passport${files.length > 1 ? 's' : ''}`}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
