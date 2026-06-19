import { useState, useEffect, useRef } from 'react'
import { apiGet } from './api'

export function useSearch() {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searchError, setSearchError] = useState(false)
  const [searchLoading, setSearchLoading] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)
  const [highlightIndex, setHighlightIndex] = useState(-1)
  const [typeFilter, setTypeFilter] = useState(null)
  const searchBoxRef = useRef(null)
  const resultRefs = useRef([])

  // 실시간 검색 — 입력이 바뀌면 250ms 디바운스 후 자동 조회. 직전 요청은 abort로 경쟁 차단.
  // setState는 전부 setTimeout/async 콜백 안에서만(effect 동기 본문 setState 금지 — react-hooks v7).
  useEffect(() => {
    const q = searchQuery.trim()
    if (!q) return
    const ctrl = new AbortController()
    const timer = setTimeout(async () => {
      setSearchLoading(true)
      try {
        const data = await apiGet(`/search?q=${encodeURIComponent(q)}`, { signal: ctrl.signal })
        setSearchResults(data)
        setSearchError(false)
      } catch (e) {
        if (e.name === 'AbortError') return // 더 최신 입력이 진행 중 — 무시
        setSearchResults([]); setSearchError(true)
      }
      setSearchLoading(false)
      setShowDropdown(true)
      setHighlightIndex(-1)
      setTypeFilter(null)
    }, 250)
    return () => { clearTimeout(timer); ctrl.abort() }
  }, [searchQuery])

  // 드롭다운 바깥 클릭 시 닫기
  useEffect(() => {
    if (!showDropdown) return
    const onDown = (e) => {
      if (searchBoxRef.current && !searchBoxRef.current.contains(e.target)) setShowDropdown(false)
    }
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [showDropdown])

  // 키보드 하이라이트가 보이도록 스크롤
  useEffect(() => {
    if (highlightIndex >= 0) resultRefs.current[highlightIndex]?.scrollIntoView({ block: 'nearest' })
  }, [highlightIndex])

  function onSearchInput(e) {
    const v = e.target.value
    setSearchQuery(v)
    if (!v.trim()) { setSearchResults([]); setSearchError(false); setSearchLoading(false); setShowDropdown(false) }
  }

  function clearSearch() {
    setSearchQuery('')
    setSearchResults([])
    setShowDropdown(false)
    setHighlightIndex(-1)
    setTypeFilter(null)
  }

  const typeCounts = searchResults.reduce((m, r) => { m[r.label] = (m[r.label] || 0) + 1; return m }, {})
  const filteredResults = typeFilter ? searchResults.filter(r => r.label === typeFilter) : searchResults

  return {
    searchQuery, searchResults, searchError, searchLoading,
    showDropdown, setShowDropdown,
    highlightIndex, setHighlightIndex,
    typeFilter, setTypeFilter,
    typeCounts, filteredResults,
    searchBoxRef, resultRefs,
    onSearchInput, clearSearch,
  }
}
