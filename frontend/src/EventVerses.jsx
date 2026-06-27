import { useState, useEffect } from 'react'
import { apiGet } from './api'
import VerseLangTabs from './VerseLangTabs'
import Spinner from './Spinner'

// 사건(Event)의 근거구절을 권별로 표시 — 여정 정차지 선택 시 JourneyList(데스크톱)·
// 모바일 여정 칩이 공유. 데이터·렌더는 SidePanel의 Place 구절 드릴다운과 동일
// (/event/{id}/verses, books[].verses[].textKo/En, ADR-0003 프리베이크 본문).
// 선택 자체가 펼침 행위이므로 별도 접기/펼치기 없이 구절을 바로 보인다.

const BOOK_COLOR = '#a78bfa'

const boxStyle = {
  margin: '4px 0 6px',
  padding: '8px 10px',
  background: '#f5f3ff',
  borderLeft: `3px solid ${BOOK_COLOR}`,
  borderRadius: 6,
  fontSize: 12,
}

const chipBase = {
  display: 'inline-flex', alignItems: 'center',
  fontSize: 11, padding: '1px 7px', borderRadius: 999, lineHeight: 1.7,
  border: `1px solid ${BOOK_COLOR}`, cursor: 'pointer', fontWeight: 600,
}

export default function EventVerses({ eventId, verseLang, setVerseLang }) {
  // state.id로 어느 eventId의 결과인지 추적 — eventId 변경 시 state.id≠eventId라 자동으로
  // 로딩(스피너)이 되고, setState는 async 콜백에서만 호출(set-state-in-effect 준수, SidePanel 패턴).
  // bookId(권 선택)도 .then에서만 갱신 — eventId 변경 중에는 ready=false라 읽지 않는다.
  const [state, setState] = useState({ id: null, data: null })
  const [bookId, setBookId] = useState(null)

  useEffect(() => {
    if (!eventId) return
    let cancelled = false
    const ctrl = new AbortController()
    apiGet('/event/' + eventId + '/verses', { signal: ctrl.signal })
      .then(data => {
        if (cancelled) return
        setState({ id: eventId, data })
        setBookId((data.books || [])[0]?.bookId ?? null)
      })
      .catch(e => { if (!cancelled && e?.name !== 'AbortError') setState({ id: eventId, data: { books: [] } }) })
    return () => { cancelled = true; ctrl.abort() }
  }, [eventId])

  const ready = state.id === eventId
  if (!ready) {
    return <div style={boxStyle}><Spinner size={18} color="rgba(107,40,217,0.5)" /></div>
  }
  const books = state.data.books || []
  if (books.length === 0) {
    return <div style={{ ...boxStyle, color: '#8b80a8' }}>표시할 구절이 없습니다</div>
  }
  const selBook = books.find(b => b.bookId === bookId) || books[0]

  return (
    <div style={boxStyle}>
      {books.length > 1 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 6 }}>
          {books.map(b => {
            const sel = b.bookId === selBook.bookId
            return (
              <button
                key={b.bookId}
                onClick={() => setBookId(b.bookId)}
                style={{ ...chipBase, background: sel ? BOOK_COLOR : '#fff', color: sel ? '#fff' : '#5b21b6' }}
              >{b.bookNameKo || b.bookId}</button>
            )
          })}
        </div>
      )}
      <div style={{ marginBottom: 6 }}>
        <VerseLangTabs verseLang={verseLang} setVerseLang={setVerseLang} color={BOOK_COLOR} />
      </div>
      <div style={{ fontWeight: 600, color: '#6d28d9', marginBottom: 4 }}>
        {selBook.bookNameKo || selBook.bookId} {selBook.rangeLabel}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
        {selBook.verses.map(v => {
          const body = (verseLang === 'ko' ? v.textKo : v.textEn) || '원문이 없습니다'
          return (
            <div key={v.verseID} style={{ color: '#374151', lineHeight: 1.5 }}>
              <span style={{ fontWeight: 600, color: '#6d28d9', marginRight: 6 }}>{v.chapter}:{v.verse}</span>
              {body}
            </div>
          )
        })}
      </div>
    </div>
  )
}
