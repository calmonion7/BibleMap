import { useState, useCallback, useMemo } from 'react'

// 읽기 진도(task#269) — 장 단위 읽음 표시. 북마크와 같은 저장 관행을 따른다: `biblemap-` 접두사,
// 스키마 버전 필드, 파손·구버전은 마이그레이션 없이 빈 값 폴백(ADR 260819-191704).
const KEY = 'biblemap-read'
const SCHEMA_V = 1

// { v:1, books: { [bookId]: number[] }, last: { bookId, chapter, label } | null }
const EMPTY = { books: {}, last: null }

function read() {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return EMPTY
    const parsed = JSON.parse(raw)
    if (!parsed || parsed.v !== SCHEMA_V || !parsed.books || typeof parsed.books !== 'object') return EMPTY
    const books = {}
    for (const [id, list] of Object.entries(parsed.books)) {
      if (Array.isArray(list)) books[id] = list.filter(n => Number.isInteger(n) && n > 0)
    }
    return { books, last: parsed.last ?? null }
  } catch (e) {
    console.warn(`[useReadingProgress] ${KEY} 파손 — 빈 진도로 폴백`, e)
    return EMPTY
  }
}

function write(state) {
  try {
    localStorage.setItem(KEY, JSON.stringify({ v: SCHEMA_V, books: state.books, last: state.last }))
  } catch (e) {
    console.warn(`[useReadingProgress] ${KEY} 저장 실패 — 이번 변경은 이 기기에 남지 않음`, e)
  }
}

export function useReadingProgress() {
  const [state, setState] = useState(read)

  const isRead = useCallback((bookId, chapter) => !!state.books[bookId]?.includes(chapter), [state])

  const toggleRead = useCallback((bookId, chapter, label) => {
    if (!bookId || !chapter) return
    setState(prev => {
      const cur = prev.books[bookId] || []
      const has = cur.includes(chapter)
      const nextList = has ? cur.filter(n => n !== chapter) : [...cur, chapter].sort((a, b) => a - b)
      const books = { ...prev.books }
      if (nextList.length) books[bookId] = nextList
      else delete books[bookId]
      // 읽음 표시는 마지막 위치를 갱신하고, 해제는 옮기지 않는다(이어읽기가 뒤로 튀지 않게).
      // 단 그 책의 읽은 장이 0이 되면 그 책을 가리키던 마지막 위치는 지운다.
      let last = prev.last
      if (!has) last = { bookId, chapter, label: label ?? null }
      else if (!books[bookId] && last?.bookId === bookId) last = null
      const next = { books, last }
      write(next)
      return next
    })
  }, [])

  // 책별 읽은 장 수 · 전체 읽은 장 수
  const bookReadCount = useCallback(bookId => state.books[bookId]?.length ?? 0, [state])
  const totalRead = useMemo(
    () => Object.values(state.books).reduce((n, list) => n + list.length, 0),
    [state],
  )

  // 이어읽기 — 마지막으로 읽은 책에서 아직 읽지 않은 가장 앞 장.
  const resume = useMemo(() => {
    const last = state.last
    if (!last?.bookId) return null
    const set = new Set(state.books[last.bookId] || [])
    let n = 1
    while (set.has(n)) n += 1
    return { bookId: last.bookId, chapter: n, label: last.label ?? null }
  }, [state])

  return { readBooks: state.books, isRead, toggleRead, bookReadCount, totalRead, resume }
}
