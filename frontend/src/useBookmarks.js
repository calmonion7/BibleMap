import { useState, useCallback } from 'react'

// 개인화 저장 계층(task#268) — 북마크와 이어보기. 서버 쓰기 경로 없이 이 기기에만 남는다
// (ADR `260819-191704-personalization-localstorage-only`). 스키마는 버전 필드를 갖고,
// 파손·구버전은 마이그레이션 없이 빈 목록으로 폴백한다(개인화는 유실돼도 앱이 망가지지 않는 데이터).
const BOOKMARKS_KEY = 'biblemap-bookmarks'
const RECENT_KEY = 'biblemap-recent'
const SCHEMA_V = 1
const BOOKMARK_CAP = 100
const RECENT_CAP = 8

// 저장 항목 = { hash, type, label, ts } — hash 하나로 복원한다(urlState의 해시 코덱 재사용).
function read(key) {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!parsed || parsed.v !== SCHEMA_V || !Array.isArray(parsed.items)) return []
    return parsed.items.filter(it => it && typeof it.hash === 'string' && it.hash)
  } catch (e) {
    console.warn(`[useBookmarks] ${key} 파손 — 빈 목록으로 폴백`, e)
    return []
  }
}

function write(key, items) {
  try {
    localStorage.setItem(key, JSON.stringify({ v: SCHEMA_V, items }))
  } catch (e) {
    console.warn(`[useBookmarks] ${key} 저장 실패 — 이번 변경은 이 기기에 남지 않음`, e)
  }
}

export function useBookmarks() {
  const [bookmarks, setBookmarks] = useState(() => read(BOOKMARKS_KEY))
  const [recent, setRecent] = useState(() => read(RECENT_KEY))

  const toggleBookmark = useCallback(entry => {
    if (!entry?.hash) return
    setBookmarks(prev => {
      const exists = prev.some(b => b.hash === entry.hash)
      const next = exists
        ? prev.filter(b => b.hash !== entry.hash)
        : [{ ...entry, ts: Date.now() }, ...prev].slice(0, BOOKMARK_CAP)
      write(BOOKMARKS_KEY, next)
      return next
    })
  }, [])

  const removeBookmark = useCallback(hash => {
    setBookmarks(prev => {
      const next = prev.filter(b => b.hash !== hash)
      write(BOOKMARKS_KEY, next)
      return next
    })
  }, [])

  // 같은 화면을 다시 보면 새 항목을 쌓지 않고 최신으로 승격한다(중복 제거 후 맨 앞).
  const recordRecent = useCallback(entry => {
    if (!entry?.hash) return
    setRecent(prev => {
      const head = prev[0]
      if (head && head.hash === entry.hash && head.label === entry.label) return prev
      const next = [{ ...entry, ts: Date.now() }, ...prev.filter(r => r.hash !== entry.hash)].slice(0, RECENT_CAP)
      write(RECENT_KEY, next)
      return next
    })
  }, [])

  return { bookmarks, recent, toggleBookmark, removeBookmark, recordRecent }
}
