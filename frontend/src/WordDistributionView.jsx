import { useState, useEffect } from 'react'
import { apiGet } from './api'
import Spinner from './Spinner'
import VerseLangTabs from './VerseLangTabs'

// 단어 분포 페이지 — 책(또는 성경 전체)의 상위 빈도 명사를 감정 극성(긍정/중립/부정)
// 3영역 타이포그래피 클라우드로 표시. 크기 ∝ √빈도, 단어 탭 → 해당 책의 포함 구절 시트.
// 데이터는 빌드타임 정본(word_distribution.json)을 /words API가 서빙(런타임 형태소 분석 없음).

const BANDS = [
  { key: 'positive', label: '긍정', color: 'var(--valence-pos)' },
  { key: 'neutral', label: '중립', color: 'var(--valence-neutral)' },
  { key: 'negative', label: '부정', color: 'var(--valence-neg)' },
]

// 폰트 크기: √(빈도/최대빈도)로 13~34px — 선형이면 최고빈도어(하나님·여호와)가 화면을 삼킨다
function fontSize(count, max) {
  return Math.round(13 + 21 * Math.sqrt(count / max))
}

function WordDistributionView({ bookId, onSelectBook, verseLang, setVerseLang }) {
  const [data, setData] = useState(null)       // /words/{bookId} 응답
  const [failed, setFailed] = useState(false)
  const [books, setBooks] = useState(null)     // 책 선택 드롭다운(1회 로드)
  const [verseView, setVerseView] = useState(null) // { word, color, loading, total, verses } | null

  useEffect(() => {
    let cancelled = false
    apiGet('/books-overview')
      .then(list => { if (!cancelled) setBooks(list) })
      .catch(e => { if (!cancelled) console.warn('[WordDistribution] 책 목록 로드 실패 — 드롭다운 미노출', e) })
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    const ctrl = new AbortController()
    setData(null); setFailed(false); setVerseView(null)
    apiGet(`/words/${encodeURIComponent(bookId)}`, { signal: ctrl.signal })
      .then(setData)
      .catch(e => { if (e?.name !== 'AbortError') { console.warn('[WordDistribution] 단어 분포 로드 실패', e); setFailed(true) } })
    return () => ctrl.abort()
  }, [bookId])

  function openWord(word, color) {
    setVerseView({ word, color, loading: true, total: 0, verses: [] })
    apiGet(`/words/${encodeURIComponent(bookId)}/verses?w=${encodeURIComponent(word)}`)
      .then(({ total, verses }) => setVerseView(v => (v && v.word === word ? { ...v, loading: false, total, verses } : v)))
      .catch(e => { console.warn('[WordDistribution] 구절 검색 실패', e); setVerseView(v => (v && v.word === word ? { ...v, loading: false } : v)) })
  }

  const maxCount = data?.words?.length ? data.words[0].count : 1
  const title = bookId === 'all' ? '성경 전체' : (data?.nameKo || '')

  return (
    <div style={{ height: '100%', overflowY: 'auto', background: 'var(--bg-0)', position: 'relative' }}>
      <div style={{ maxWidth: 720, margin: '0 auto', padding: '16px 16px 64px' }}>
        {/* 헤더 — 제목 + 책 선택 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginBottom: 4 }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: 'var(--ink)', fontFamily: 'var(--serif)' }}>
            {title} 단어 분포
          </h2>
          {books && (
            <select
              value={bookId}
              onChange={e => onSelectBook(e.target.value)}
              style={{
                font: 'inherit', fontSize: 13, padding: '5px 8px', borderRadius: 8,
                background: 'var(--bg-2)', color: 'var(--ink-dim)', border: '1px solid var(--line-strong)',
              }}
            >
              <option value="all">성경 전체</option>
              {books.map(b => <option key={b.id} value={b.id}>{b.nameKo}</option>)}
            </select>
          )}
        </div>
        <div style={{ fontSize: 12, color: 'var(--ink-faint)', marginBottom: 18 }}>
          자주 나오는 단어일수록 크게 표시됩니다 · 단어를 누르면 그 단어가 나오는 구절을 보여줍니다
        </div>

        {failed && <div style={{ color: 'var(--danger)', fontSize: 13 }}>단어 분포를 불러오지 못했습니다.</div>}
        {!data && !failed && <Spinner />}

        {data && BANDS.map(band => {
          const words = data.words.filter(w => w.polarity === band.key)
          return (
            <div key={band.key} style={{ marginBottom: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 8 }}>
                <span style={{ width: 9, height: 9, borderRadius: '50%', background: band.color }} />
                <span style={{ fontSize: 12, fontWeight: 700, color: band.color }}>{band.label}</span>
                <span style={{ fontSize: 11, color: 'var(--ink-faint)' }}>{words.length}</span>
              </div>
              <div style={{
                display: 'flex', flexWrap: 'wrap', alignItems: 'baseline', gap: '4px 12px',
                padding: '14px 14px', borderRadius: 12,
                background: 'var(--bg-1)', border: '1px solid var(--line)',
              }}>
                {words.length === 0 && <span style={{ fontSize: 12, color: 'var(--ink-faint)' }}>해당 단어 없음</span>}
                {words.map(w => (
                  <button
                    key={w.word}
                    onClick={() => openWord(w.word, band.color)}
                    title={`${w.count}회`}
                    style={{
                      border: 'none', background: 'none', cursor: 'pointer', padding: 0,
                      fontFamily: 'var(--serif)', fontWeight: 600, lineHeight: 1.35,
                      fontSize: fontSize(w.count, maxCount), color: band.color,
                      opacity: 0.55 + 0.45 * Math.sqrt(w.count / maxCount),
                    }}
                  >{w.word}</button>
                ))}
              </div>
            </div>
          )
        })}
      </div>

      {/* 구절 시트 — 단어 탭 시 하단에서 열림(모바일·데스크톱 공통) */}
      {verseView && (
        <div style={{
          position: 'fixed', left: 0, right: 0, bottom: 0, zIndex: 30,
          maxHeight: '55dvh', display: 'flex', flexDirection: 'column',
          background: 'var(--bg-1)', borderTop: '1px solid var(--line-strong)', boxShadow: 'var(--shadow-2)',
        }}>
          <div style={{ maxWidth: 720, margin: '0 auto', width: '100%', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px 8px', flexShrink: 0 }}>
              <span style={{ fontSize: 17, fontWeight: 700, fontFamily: 'var(--serif)', color: verseView.color }}>{verseView.word}</span>
              {!verseView.loading && <span style={{ fontSize: 12, color: 'var(--ink-faint)' }}>{verseView.total}구절{verseView.total > verseView.verses.length ? ` 중 ${verseView.verses.length}` : ''}</span>}
              <VerseLangTabs verseLang={verseLang} setVerseLang={setVerseLang} color="var(--gold)" />
              <button
                onClick={() => setVerseView(null)}
                aria-label="닫기"
                style={{ marginLeft: 'auto', border: 'none', background: 'none', cursor: 'pointer', color: 'var(--ink-faint)', fontSize: 16, padding: 4 }}
              >✕</button>
            </div>
            <div style={{ overflowY: 'auto', padding: '0 16px 20px' }}>
              {verseView.loading && <Spinner />}
              {!verseView.loading && verseView.verses.length === 0 && (
                <div style={{ fontSize: 13, color: 'var(--ink-faint)', padding: '8px 0' }}>구절을 찾지 못했습니다.</div>
              )}
              {verseView.verses.map(v => (
                <div key={v.ref + v.textKo.slice(0, 8)} style={{ padding: '8px 0', borderBottom: '1px solid var(--line)' }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--gold)', marginBottom: 3 }}>{v.ref}</div>
                  <div style={{ fontSize: 13, color: 'var(--ink-dim)', lineHeight: 1.65 }}>
                    {verseLang === 'en' && v.textEn ? v.textEn : v.textKo}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default WordDistributionView
