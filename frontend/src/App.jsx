import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Classifier from './pages/Classifier'

export default function App() {
  return (
    <BrowserRouter>
      <main className="min-h-screen bg-slate-50">
        <Routes>
          <Route path="/" element={<Classifier />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
