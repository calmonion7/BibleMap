import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// 라이트 테마(Day Atlas)는 옵트인 — 렌더 전에 동기 반영해 첫 페인트 깜빡임 방지(ADR-0020)
if (localStorage.getItem('biblemap-theme') === 'light') {
  document.documentElement.dataset.theme = 'light'
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
