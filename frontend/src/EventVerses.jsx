import { useState, useEffect } from 'react'
import { apiGet } from './api'
import VerseLangTabs from './VerseLangTabs'
import Spinner from './Spinner'

// 사건(Event)의 근거구절을 권별로 표시 — 여정 정차지 선택 시 JourneyList(데스크톱)·
// 모바일 여정 칩이 공유. 데이터·렌더는 SidePanel의 Place 구절 드릴다운과 동일
// (/event/{id}/verses, books[].verses[].textKo/En, ADR-0003 프리베이크 본문).
// 선택 자체가 펼침 행위이므로 별도 접기/펼치기 없이 구절을 바로 보인다.
//
// heading/onClose가 주어지면 "읽기 모드"(모바일): 사건명·권 칩·한/영 탭을 상단에
// 고정하고 절 본문만 독립 스크롤한다(긴 구절 1000+절도 흡수). 없으면(데스크톱 인라인)
// 기존 렌더 그대로.

const BOOK_COLOR = '#a78bfa'

const boxStyle = {
  margin: '4px 0 6px',
  padding: '8px 10px',
  background: '#f5f3ff',
  borderLeft: `3px solid ${BOOK_COLOR}`,
  borderRadius: 6,
  fontSize: 12,
}

// 읽기 모드 전용 스타일 — 세로 flex: 상단 고정 헤더 + 하단 스크롤 본문
const readWrapStyle = { height: '100%', display: 'flex', flexDirection: 'column', background: '#faf9ff' }
const readHeadStyle = {
  flex: 'none', display: 'flex', alignItems: 'center', gap: 8,
  padding: '10px 14px', borderBottom: '1px solid #e7e3f5', background: '#fff',
}
const readTopStyle = { flex: 'none', padding: '8px 14px 6px', borderBottom: '1px solid #efecf8', background: '#fff' }
const readBodyStyle = { flex: 1, minHeight: 0, overflowY: 'auto', WebkitOverflowScrolling: 'touch', padding: '10px 14px 16px', fontSize: 13 }
const closeBtnStyle = {
  flex: 'none', border: `1px solid ${BOOK_COLOR}`, background: 'rgba(167,139,250,0.14)',
  color: '#6d28d9', borderRadius: 999, padding: '8px 12px', fontSize: 12, fontWeight: 700, cursor: 'pointer',
}

const chipBase = {
  display: 'inline-flex', alignItems: 'center',
  fontSize: 11, padding: '1px 7px', borderRadius: 999, lineHeight: 1.7,
  border: `1px solid ${BOOK_COLOR}`, cursor: 'pointer', fontWeight: 600,
}

export default function EventVerses({ eventId, verseLang, setVerseLang, heading, onClose }) {
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

  const reading = onClose != null
  // 읽기 모드: 상단 고정 헤더(사건명 + 여정으로 닫기). 로딩·빈 상태에서도 헤더를 유지해 되돌아갈 수 있게 한다.
  const readHeader = reading && (
    <div style={readHeadStyle}>
      <div style={{ flex: 1, minWidth: 0, fontSize: 14, fontWeight: 800, color: '#1b1e3a' }}>{heading}</div>
      <button onClick={onClose} aria-label="여정으로 돌아가기" style={closeBtnStyle}>▾ 여정으로</button>
    </div>
  )

  const ready = state.id === eventId
  if (!ready) {
    const spin = <div style={boxStyle}><Spinner size={18} color="rgba(107,40,217,0.5)" /></div>
    return reading
      ? <div style={readWrapStyle}>{readHeader}<div style={readBodyStyle}>{spin}</div></div>
      : spin
  }
  const books = state.data.books || []
  if (books.length === 0) {
    const empty = <div style={{ ...boxStyle, color: '#8b80a8' }}>표시할 구절이 없습니다</div>
    return reading
      ? <div style={readWrapStyle}>{readHeader}<div style={readBodyStyle}>{empty}</div></div>
      : empty
  }
  const selBook = books.find(b => b.bookId === bookId) || books[0]

  const bookChips = books.length > 1 && (
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
  )
  const langTabs = (
    <div style={{ marginBottom: 6 }}>
      <VerseLangTabs verseLang={verseLang} setVerseLang={setVerseLang} color={BOOK_COLOR} />
    </div>
  )
  const refLabel = (
    <div style={{ fontWeight: 600, color: '#6d28d9', marginBottom: 4 }}>
      {selBook.bookNameKo || selBook.bookId} {selBook.rangeLabel}
    </div>
  )
  const verseList = (
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
  )

  // 읽기 모드: 권 칩·언어 탭·범위 라벨은 상단 고정(스크롤과 분리), 절 본문만 스크롤.
  if (reading) {
    return (
      <div style={readWrapStyle}>
        {readHeader}
        <div style={readTopStyle}>{bookChips}{langTabs}{refLabel}</div>
        <div style={readBodyStyle}>{verseList}</div>
      </div>
    )
  }

  return (
    <div style={boxStyle}>
      {bookChips}
      {langTabs}
      {refLabel}
      {verseList}
    </div>
  )
}
